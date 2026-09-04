import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- Konfigurasi File ---
FILE_MENU = 'Menu_makanan.xlsx'
FILE_JURNAL = 'jurnal_konsumen.xlsx'

# --- Fungsi untuk Memuat Data ---
@st.cache_data
def muat_data():
    """Memuat data dari file Excel."""
    try:
        menu_df = pd.read_excel(FILE_MENU)
        jurnal_df = pd.read_excel(FILE_JURNAL)
        return menu_df, jurnal_df
    except FileNotFoundError:
        st.error(f"Error: File '{FILE_MENU}' atau '{FILE_JURNAL}' tidak ditemukan. Pastikan file-file tersebut ada.")
        return None, None
    except Exception as e:
        st.error(f"Error saat memuat data: {e}")
        return None, None

# --- Fungsi untuk Menyimpan Data ---
def simpan_data(menu_df, jurnal_df):
    """Menyimpan perubahan ke file Excel."""
    try:
        menu_df.to_excel(FILE_MENU, index=False)
        jurnal_df.to_excel(FILE_JURNAL, index=False)
        st.success("✅ Data berhasil disimpan.")
    except Exception as e:
        st.error(f"❌ Error saat menyimpan data: {e}")

# --- Fungsi Pemesanan Pelanggan + TOMBOL HAPUS ---
def proses_pesanan(menu_df, jurnal_df):
    """Memproses pesanan pelanggan — bisa tambah, lihat tabel, dan HAPUS item."""
    st.subheader("Pesan Menu")

    # === PENAMPUNG PESANAN (tetap terjaga selama sesi) ===
    if 'pesanan_saat_ini' not in st.session_state:
        st.session_state.pesanan_saat_ini = {}  # {'Nama Menu': {detail}}
    if 'nama_pelanggan' not in st.session_state:
        st.session_state.nama_pelanggan = ""
    if 'nomor_meja' not in st.session_state:
        st.session_state.nomor_meja = ""

    # Tampilkan daftar menu
    st.write("📋 **Daftar Menu:**")
    menu_tampil = menu_df[['Menu', 'Harga', 'Stok']].copy()
    menu_tampil.index = menu_tampil.index + 1
    st.dataframe(menu_tampil, use_container_width=True)

    # Input identitas pelanggan
    st.session_state.nama_pelanggan = st.text_input("Nama Pelanggan:", value=st.session_state.nama_pelanggan)
    st.session_state.nomor_meja = st.text_input("Nomor Meja (Opsional):", value=st.session_state.nomor_meja)

    st.write("--- ➕ Tambah Pesanan ---")

    # Pilih menu dan jumlah
    pilihan_menu_str = st.selectbox("Pilih Menu:", [''] + menu_df['Menu'].tolist())
    jml_pesan_input = 0

    if pilihan_menu_str:
        try:
            menu_terpilih = menu_df[menu_df['Menu'] == pilihan_menu_str].iloc[0]
            harga_satuan = menu_terpilih['Harga']
            stok_tersedia = menu_terpilih['Stok']

            jml_pesan_input = st.number_input(
                f"Jumlah '{pilihan_menu_str}' (Stok: {stok_tersedia}):",
                min_value=0, value=0, step=1
            )

            if jml_pesan_input > 0:
                if jml_pesan_input <= stok_tersedia:
                    total_harga_item = harga_satuan * jml_pesan_input
                    # Simpan ke penampung (bisa tambah/ganti jumlah)
                    st.session_state.pesanan_saat_ini[pilihan_menu_str] = {
                        'Jml_pesan': jml_pesan_input,
                        'Harga_Satuan': harga_satuan,
                        'Jml_Harga': total_harga_item
                    }
                    st.success(f"✅ '{pilihan_menu_str}' × {jml_pesan_input} = Rp {total_harga_item:,.0f} ditambahkan!")
                else:
                    st.warning(f"⚠️ Stok tidak cukup! Tersedia: {stok_tersedia}")
        except Exception as e:
            st.error(f"❌ Kesalahan: {e}")

    # === TABEL PESANAN SAAT INI + TOMBOL HAPUS ===
    st.write("--- 📝 Pesanan Anda Saat Ini ---")
    if st.session_state.pesanan_saat_ini:
        
        # Tampilkan setiap item dengan tombol HAPUS
        items_dihapus = []
        
        for menu, detail in st.session_state.pesanan_saat_ini.items():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
            with col1:
                st.write(f"**{menu}**")
            with col2:
                st.write(f"× {detail['Jml_pesan']}")
            with col3:
                st.write(f"Rp {detail['Harga_Satuan']:,.0f}")
            with col4:
                st.write(f"**Rp {detail['Jml_Harga']:,.0f}**")
            with col5:
                if st.button("🗑️", key=f"hapus_{menu}"):
                    items_dihapus.append(menu)
                    st.rerun()  # Segera refresh tampilan
        
        # Hapus item yang ditekan tombolnya
        for menu in items_dihapus:
            del st.session_state.pesanan_saat_ini[menu]
            st.warning(f"🗑️ '{menu}' telah dihapus dari pesanan.")
            st.rerun()

        # Hitung total keseluruhan
        total_keseluruhan = sum(d['Jml_Harga'] for d in st.session_state.pesanan_saat_ini.values())
        st.info(f"💰 **Total Keseluruhan: Rp {total_keseluruhan:,.0f}**")

        # Tombol simpan pesanan
        if st.button("✅ Selesaikan & Simpan Pesanan"):
            if not st.session_state.nama_pelanggan:
                st.warning("⚠️ Silakan isi Nama Pelanggan terlebih dahulu!")
            else:
                tanggal_sekarang = datetime.now().strftime('%d-%b-%y')
                keterangan = f"Meja {st.session_state.nomor_meja}" if st.session_state.nomor_meja else ""

                # Simpan setiap item ke jurnal
                for menu, detail in st.session_state.pesanan_saat_ini.items():
                    data_baru = {
                        'Tanggal': tanggal_sekarang,
                        'Pelanggan': st.session_state.nama_pelanggan,
                        'Menu_dipesan': menu,
                        'Jml_pesan': detail['Jml_pesan'],
                        'Harga_Satuan': detail['Harga_Satuan'],
                        'Jml_Harga': detail['Jml_Harga'],
                        'Keterangan': keterangan
                    }
                    new_row_df = pd.DataFrame([data_baru])
                    jurnal_df = pd.concat([jurnal_df, new_row_df], ignore_index=True)
                    # Kurangi stok
                    menu_df.loc[menu_df['Menu'] == menu, 'Stok'] -= detail['Jml_pesan']

                simpan_data(menu_df, jurnal_df)
                st.success(f"🎉 Pesanan atas nama **{st.session_state.nama_pelanggan}** tersimpan!")

                # Kosongkan pesanan setelah selesai
                st.session_state.pesanan_saat_ini.clear()
                st.session_state.nama_pelanggan = ""
                st.session_state.nomor_meja = ""
                st.rerun()
    else:
        st.info("Belum ada pesanan. Silakan pilih menu di atas.")

    return menu_df, jurnal_df

# --- Fungsi Laporan Monitor Warung ---
def tampilkan_laporan(jurnal_df):
    """Menampilkan laporan jumlah konsumen dan total penjualan berdasarkan tanggal."""
    st.subheader("📊 Laporan Monitor Warung")

    if jurnal_df.empty:
        st.warning("⚠️ Belum ada data transaksi.")
        return

    if 'Tanggal' not in jurnal_df.columns:
        st.warning("⚠️ Kolom 'Tanggal' tidak ditemukan.")
        return

    # Konversi tanggal dengan toleransi format
    jurnal_df['Tanggal_dt'] = pd.to_datetime(jurnal_df['Tanggal'], format='%d-%b-%y', errors='coerce')
    jurnal_df.dropna(subset=['Tanggal_dt'], inplace=True)

    tanggal_laporan_str = st.text_input(
        "Masukkan tanggal untuk laporan (contoh: 03-Sep-26, atau biarkan kosong untuk SEMUA):"
    )

    laporan_terfilter = jurnal_df.copy()
    tanggal_dipilih_str = "SEMUA TANGGAL"

    if tanggal_laporan_str:
        try:
            tgl_input = datetime.strptime(tanggal_laporan_str, '%d-%b-%y')
            laporan_terfilter = jurnal_df[jurnal_df['Tanggal_dt'].dt.date == tgl_input.date()]
            tanggal_dipilih_str = tanggal_laporan_str
        except ValueError:
            st.warning("⚠️ Format tanggal salah — menampilkan SEMUA data.")

    st.write(f"📅 Laporan untuk: **{tanggal_dipilih_str}**")

    if laporan_terfilter.empty:
        st.warning("⚠️ Tidak ada transaksi pada tanggal tersebut.")
    else:
        jumlah_konsumen = laporan_terfilter['Pelanggan'].nunique()
        total_penjualan = laporan_terfilter['Jml_Harga'].sum()

        st.metric("👥 Jumlah Konsumen Unik", jumlah_konsumen)
        st.metric("💰 Total Penjualan", f"Rp {total_penjualan:,.0f}")

        st.write("--- 📋 Detail Transaksi ---")
        st.dataframe(
            laporan_terfilter[['Tanggal', 'Pelanggan', 'Menu_dipesan', 'Jml_pesan', 'Jml_Harga', 'Keterangan']],
            use_container_width=True
        )

# --- Fungsi Upload File ---
def upload_file():
    st.sidebar.subheader("📂 Upload File")
    uploaded_menu = st.sidebar.file_uploader("Pilih file Menu_makanan.xlsx", type=["xlsx"])
    uploaded_jurnal = st.sidebar.file_uploader("Pilih file jurnal_konsumen.xlsx", type=["xlsx"])

    menu_df = None
    jurnal_df = None
    if uploaded_menu:
        try:
            menu_df = pd.read_excel(uploaded_menu)
            st.sidebar.success("✅ Menu_makanan.xlsx terbaca")
        except Exception as e:
            st.sidebar.error(f"❌ Error baca Menu: {e}")
    if uploaded_jurnal:
        try:
            jurnal_df = pd.read_excel(uploaded_jurnal)
            st.sidebar.success("✅ jurnal_konsumen.xlsx terbaca")
        except Exception as e:
            st.sidebar.error(f"❌ Error baca Jurnal: {e}")
    return menu_df, jurnal_df

# --- Main App ---
def main():
    st.title("🏪 Aplikasi Warung Matera")

    opsi_data = st.sidebar.radio("📂 Sumber Data", ("Gunakan File Lokal", "Upload File"))
    menu_df = None
    jurnal_df = None

    if opsi_data == "Gunakan File Lokal":
        try:
            pd.read_excel(FILE_MENU)
            pd.read_excel(FILE_JURNAL)
            menu_df, jurnal_df = muat_data()
        except FileNotFoundError:
            st.warning("⚠️ File Excel tidak ditemukan! Gunakan opsi Upload File.")
            return
    else:
        menu_df, jurnal_df = upload_file()

    if menu_df is not None and jurnal_df is not None:
        # Pastikan kolom Tanggal ada
        if 'Tanggal' not in jurnal_df.columns:
            jurnal_df['Tanggal'] = ''

        st.sidebar.header("📋 Menu Aplikasi")
        pilihan = st.sidebar.radio("Pilih Aksi:", [
            "Pesan Menu",
            "Laporan Warung",
            "Lihat Data Menu",
            "Lihat Data Jurnal"
        ])

        if pilihan == "Pesan Menu":
            menu_df, jurnal_df = proses_pesanan(menu_df, jurnal_df)
        elif pilihan == "Laporan Warung":
            tampilkan_laporan(jurnal_df)
        elif pilihan == "Lihat Data Menu":
            st.subheader("📋 Data Menu Makanan")
            st.dataframe(menu_df, use_container_width=True)
        elif pilihan == "Lihat Data Jurnal":
            st.subheader("📖 Data Jurnal Konsumen")
            st.dataframe(jurnal_df, use_container_width=True)

if __name__ == "__main__":
    main()