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
        
        st.cache_data.clear()  # mengosongkan data chache

    except Exception as e:
        st.error(f"❌ Error saat menyimpan data: {e}")

# --- Fungsi Pemesanan Pelanggan + TOMBOL HAPUS ---
def proses_pesanan(menu_df, jurnal_df):
    """Memproses pesanan pelanggan — bisa tambah, lihat tabel, dan HAPUS item."""
    st.subheader("Pesan Menu")

    # ==================================================
    # ✅ INISIALISASI SESSION_STATE — SOLUSI UTAMA!
    # ==================================================
    if 'pesanan_saat_ini' not in st.session_state:
        st.session_state.pesanan_saat_ini = {}

    if 'nama_pelanggan' not in st.session_state:
        st.session_state.nama_pelanggan = ""

    if 'nomor_meja' not in st.session_state:
        st.session_state.nomor_meja = ""

    # ✅ Inisialisasi jurnal_df di session_state jika BELUM ADA
    if 'jurnal_df' not in st.session_state:
        st.session_state.jurnal_df = jurnal_df.copy()

    # ✅ Inisialisasi menu_df di session_state jika BELUM ADA
    if 'menu_df' not in st.session_state:
        st.session_state.menu_df = menu_df.copy()
    # ==================================================

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

        # ✅ Inisialisasi penampung hapus di session_state
        if 'daftar_hapus' not in st.session_state:
            st.session_state.daftar_hapus = []

        # Tampilkan setiap item dengan tombol HAPUS
        for menu, detail in st.session_state.pesanan_saat_ini.items():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
            with col1:
                st.write(f"**{menu}**")
            with col2:
                st.write(f"× {detail['Jml_pesan']}")
            with col3:
                st.write(f"Rp. {detail['Harga_Satuan']:,.0f},-".replace(",", "."))
            with col4:
                st.write(f"**Rp {detail['Jml_Harga']:,.0f}**")
            with col5:
                if st.button("🗑️", key=f"hapus_{menu}"):
                    st.session_state.daftar_hapus.append(menu)
                    st.rerun()  # Refresh setelah catat yang dihapus

        # ✅ PROSES HAPUS (berjalan setelah refresh)
        if st.session_state.daftar_hapus:
            for menu in st.session_state.daftar_hapus:
                del st.session_state.pesanan_saat_ini[menu]
                st.warning(f"🗑️ '{menu}' telah dihapus dari pesanan.")
            st.session_state.daftar_hapus = []  # Kosongkan setelah selesai
            st.rerun()

        # Hitung total keseluruhan
        total_keseluruhan = sum(d['Jml_Harga'] for d in st.session_state.pesanan_saat_ini.values())
        st.info(f"💰 **Total Keseluruhan: Rp {total_keseluruhan:,.0f}**")

        # Tombol simpan pesanan
        if st.button("✅ Selesaikan & Simpan Pesanan"):
            if not st.session_state.nama_pelanggan:
                st.warning("⚠️ Silakan isi Nama Pelanggan terlebih dahulu!")
            else:
                tanggal_sekarang = datetime.now().strftime("%d-%m-%Y")
                keterangan = f"Meja {st.session_state.nomor_meja}" if st.session_state.nomor_meja else ""

                # ✅ AMBIL dari session_state (sudah pasti ada karena diinisialisasi di atas)
                jurnal_df = st.session_state.jurnal_df.copy()
                menu_df = st.session_state.menu_df.copy()

                # Simpan setiap item ke jurnal
                for menu, detail in st.session_state.pesanan_saat_ini.items():
                    data_baru = {
                        "Tanggal": tanggal_sekarang,
                        "Pelanggan": st.session_state.nama_pelanggan,
                        "Menu_dipesan": menu,
                        "Jml_pesan": detail['Jml_pesan'],
                        "Harga_Satuan":detail['Harga_Satuan'],
                        "Jml_Harga": detail['Jml_Harga'],
                        "Keterangan": keterangan
                    }
                    new_row_df = pd.DataFrame([data_baru])
                    jurnal_df = pd.concat([jurnal_df, new_row_df], ignore_index=True)

                    # Kurangi stok
                    menu_df.loc[menu_df['Menu'] == menu, 'Stok'] -= detail['Jml_pesan']

                # ✅ SIMPAN KEMBALI KE SESSION_STATE
                st.session_state.jurnal_df = jurnal_df
                st.session_state.menu_df = menu_df

                # ✅ Simpan juga ke FILE Excel agar data tidak hilang
                simpan_data(menu_df, jurnal_df)

                st.success(f"✅ Pesanan atas nama **{st.session_state.nama_pelanggan}** tersimpan!")

                # Kosongkan pesanan setelah selesai
                st.session_state.pesanan_saat_ini.clear()
                st.session_state.nama_pelanggan = ""
                st.session_state.nomor_meja = ""
                st.rerun()
        else:
            st.info("⚠️ Belum ada pesanan. Silakan pilih menu di atas.")

    # ✅ Kembalikan DataFrame terbaru agar bisa dipakai di bagian lain
    return st.session_state.menu_df, st.session_state.jurnal_df

# --- Fungsi Laporan Monitor Warung --- ==== ini yang tampilan laporan MONITOR =====
def tampilkan_laporan(jurnal_df):
    """Menampilkan laporan + 3 grafik dalam 1 baris."""
    st.subheader("📊 Laporan Monitor Warung")
    if jurnal_df.empty:
        st.warning("⚠️ Belum ada data transaksi.")
        return
    if 'Tanggal' not in jurnal_df.columns:
        st.warning("⚠️ Kolom 'Tanggal' tidak ditemukan.")
        return

    # Konversi kolom Tanggal
    jurnal_df['Tanggal_dt'] = pd.to_datetime(jurnal_df['Tanggal'], format='%d-%m-%Y', errors='coerce')
    jurnal_df.dropna(subset=['Tanggal_dt'], inplace=True)

    # Input Tanggal Laporan
    tanggal_laporan_str = st.text_input(
        "Masukkan tanggal untuk laporan (contoh: 04-09-2026, atau biarkan kosong untuk SEMUA):"
    )
    laporan_terfilter = jurnal_df.copy()
    tanggal_dipilih_str = "SEMUA TANGGAL"

    if tanggal_laporan_str:
        try:
            from datetime import datetime
            tgl_input = datetime.strptime(tanggal_laporan_str, '%d-%m-%Y')
            laporan_terfilter = jurnal_df[jurnal_df['Tanggal_dt'].dt.date == tgl_input.date()]
            tanggal_dipilih_str = tanggal_laporan_str
        except ValueError:
            st.warning("⚠️ Format tanggal salah — menampilkan SEMUA data.")

    st.write(f"📅 Laporan untuk: **{tanggal_dipilih_str}**")

    if laporan_terfilter.empty:
        st.warning("⚠️ Tidak ada transaksi pada tanggal tersebut.")
        return

    # === METRIK UTAMA ===
    jumlah_konsumen = laporan_terfilter['Pelanggan'].nunique()
    total_penjualan = laporan_terfilter['Jml_Harga'].sum()

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("👥 Jumlah Konsumen Unik", jumlah_konsumen)
    with col_m2:
        st.metric("💰 Total Penjualan", f"Rp {total_penjualan:,.0f}")

    st.divider()

    # ==================================================
    # ✅ SIAPKAN DATA UNTUK GRAFIK
    # ==================================================
    data_tren = laporan_terfilter.copy()
    data_tren['Tanggal'] = data_tren['Tanggal_dt'].dt.strftime('%d-%m-%Y')

    # Variabel yang DIPAKAI GRAFIK — HARUS DIBUAT SEBELUM GRAFIK!
    konsumen_per_tanggal = data_tren.groupby('Tanggal')['Pelanggan'].nunique()
    menu_per_tanggal     = data_tren.groupby('Tanggal')['Jml_pesan'].sum()
    penjualan_per_tanggal = data_tren.groupby('Tanggal')['Jml_Harga'].sum()

    # ==================================================
    # ✅ 3 GRAFIK DALAM 3 KOLOM BERDAMPINGAN
    # ==================================================
    st.subheader("📈 Grafik Analisa")

    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        st.write("👥 **Jumlah Konsumen**")
        st.bar_chart(konsumen_per_tanggal, use_container_width=True, color="#4CAF50", height=250)

    with col_g2:
        st.write("🍽️ **Menu Terjual**")
        st.bar_chart(menu_per_tanggal, use_container_width=True, color="#2196F3", height=250)

    with col_g3:
        st.write("💰 **Total Penjualan (Rp)**")
        st.bar_chart(penjualan_per_tanggal, use_container_width=True, color="#FF9800", height=250)

    st.divider()

    # === TABEL DETAIL TRANSAKSI ===
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
    st.title("🏪 Aplikasi Warung Matera-01")
    st.title("Mojokerto")

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
        pilihan = st.sidebar.radio("Pilih Menu >>", [
            "Pesan Menu",
            "Laporan Warung",
            "Lihat Data Menu",
            "Lihat Data Jurnal",
            "Cetak Nota Pembayaran"            
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
        elif pilihan == "Cetak Nota Pembayaran":
            tampilkan_cetak_nota()

#======= tambahan download jurnal ====

    st.sidebar.markdown("---")
    if st.sidebar.button("📥 Download File Jurnal Pelanggan", type="primary", use_container_width=True):
        if 'jurnal_df' in st.session_state and not st.session_state.jurnal_df.empty:
            jurnal_df = st.session_state.jurnal_df.copy()
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                jurnal_df.to_excel(writer, index=False, sheet_name='Jurnal Konsumen')
            excel_data = output.getvalue()
            st.sidebar.download_button(
                label="✅ Klik untuk Unduh (.xlsx)",
                data=excel_data,
                file_name=f"Jurnal_Konsumen_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.sidebar.success(f"✅ {len(jurnal_df)} catatan siap diunduh!")
        else:
            st.sidebar.warning("⚠️ Belum ada data transaksi.")
    st.sidebar.markdown("---")
#======= batas tambahan download jurnal ====

#===== sesi tembahan =====
# --- Fungsi Cetak Nota Pembayaran ---
def tampilkan_cetak_nota():
    """Menampilkan dan mencetak nota pembayaran berdasarkan data jurnal."""
    st.subheader("🧾 Cetak Nota Pembayaran")

    # Pastikan data jurnal tersedia
    if 'jurnal_df' not in st.session_state or st.session_state.jurnal_df.empty:
        st.warning("⚠️ Belum ada data transaksi untuk dibuat nota.")
        return

    jurnal_df = st.session_state.jurnal_df.copy()

    # Pilih Nama Pelanggan dari daftar transaksi
    daftar_pelanggan = jurnal_df['Pelanggan'].dropna().unique().tolist()
    if not daftar_pelanggan:
        st.warning("⚠️ Tidak ada nama pelanggan dalam data.")
        return

    nama_pilih = st.selectbox("Pilih Nama Pelanggan:", [""] + sorted(daftar_pelanggan))

    if nama_pilih:
        # Filter transaksi pelanggan tersebut
        data_pelanggan = jurnal_df[jurnal_df['Pelanggan'] == nama_pilih].copy()

        # Ambil daftar tanggal
        daftar_tanggal = data_pelanggan['Tanggal'].dropna().unique().tolist()
        tanggal_pilih = st.selectbox("Pilih Tanggal:", [""] + sorted(daftar_tanggal, reverse=True))

        if tanggal_pilih:
            # Filter berdasarkan Pelanggan + Tanggal
            data_nota = data_pelanggan[data_pelanggan['Tanggal'] == tanggal_pilih].copy()

            if data_nota.empty:
                st.warning("⚠️ Tidak ada transaksi pada tanggal tersebut.")
                return

            # Ambil info umum (Meja)
            nomor_meja = ""
            if not data_nota['Keterangan'].isna().all():
                nomor_meja = data_nota['Keterangan'].iloc[0]

            # Hitung total
            total_bayar = data_nota['Jml_Harga'].sum()

            # === TAMPILAN NOTA ===
            st.divider()
            st.markdown(f"""
            <div style="text-align: center; font-family: monospace;">
                <h3>🏪 NOTA PEMBAYARAN</h3>
                <h4>WARUNG MATERA — MOJOKERTO</h4>
                <hr style="border: 1px dashed #aaa;"/>
                <p><strong>Nama Pelanggan :</strong> {nama_pilih}</p>
                <p><strong>Tanggal        :</strong> {tanggal_pilih}</p>
                <p><strong>Nomor Meja     :</strong> {nomor_meja if nomor_meja else '-'}</p>
                <hr style="border: 1px dashed #aaa;"/>
            </div>
            """, unsafe_allow_html=True)

            # Tabel Rincian Pesanan
            st.markdown("**Rincian Pesanan:**")

            # Tampilkan rincian
            for _, baris in data_nota.iterrows():
                menu = baris['Menu_dipesan']
                jumlah = baris['Jml_pesan']
                harga_satuan = f"Rp. {baris['Harga_Satuan']:,.0f},-".replace(",", ".")
                jumlah_harga = f"Rp. {baris['Jml_Harga']:,.0f},-".replace(",", ".")
                st.markdown(f"""
                <div style="font-family: monospace; display: flex; justify-content: space-between;">
                    <span>{menu} × {jumlah}</span>
                    <span>{jumlah_harga}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr style='border: 1px dashed #aaa;'/>", unsafe_allow_html=True)

            # Total Bayar
            total_format = f"Rp. {total_bayar:,.0f},-".replace(",", ".")
            st.markdown(f"""
            <div style="font-family: monospace; font-size: 18px; font-weight: bold; display: flex; justify-content: space-between;">
                <span>TOTAL BAYAR :</span>
                <span>{total_format}</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="text-align: center; font-family: monospace; margin-top: 20px;">
                <p>Terima Kasih atas Kunjungan Anda 🙏</p>
                <p>Semoga Selalu Berkah 🤲</p>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            # Tombol Cetak
            if st.button("🖨️ Cetak Nota"):
                st.info("💡 Tekan tombol **Cetak** di browser (Ctrl+P / ⌘+P), lalu pilih printer → Cetak!")
                st.markdown("""
                <script>window.print();</script>
                """, unsafe_allow_html=True)

            # Tampilkan juga versi teks agar bisa disalin
            with st.expander("📋 Salin Nota"):
                nota_teks = f"""
=====================================
          NOTA PEMBAYARAN
     WARUNG MATERA — MOJOKERTO
=====================================
Nama Pelanggan : {nama_pilih}
Tanggal        : {tanggal_pilih}
Nomor Meja     : {nomor_meja if nomor_meja else '-'}
-------------------------------------
Rincian Pesanan:
"""
                for _, baris in data_nota.iterrows():
                    nota_teks += f"{baris['Menu_dipesan']} × {baris['Jml_pesan']}  = Rp. {baris['Jml_Harga']:,.0f},-\n".replace(",", ".")

                nota_teks += f"""
-------------------------------------
TOTAL BAYAR    : {total_format}
=====================================
Terima Kasih 🙏
                """
                st.code(nota_teks, language="text")

# ===== menu cetak nota

if __name__ == "__main__":
    main()