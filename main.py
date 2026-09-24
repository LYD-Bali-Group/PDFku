import io
from PIL import Image
from pypdf import PdfReader, PdfWriter
import streamlit as st

st.set_page_config(
    page_title="PDF Toolset",
    page_icon="📑",
    layout="wide",
)

st.title("📑 PDF Swiss Knife")
st.caption(
    "Aplikasi manipulasi PDF lokal, aman, dan cepat tanpa kirim data ke server luar."
)

# Navigasi Tab
tab_merge, tab_split, tab_rotate, tab_protect, tab_img2pdf = st.tabs(
    [
        "🔗 Gabung PDF",
        "✂️ Pisah / Ekstrak",
        "🔄 Putar Halaman",
        "🔒 Kunci / Buka Password",
        "🖼️ Gambar ke PDF",
    ]
)

# ---------------------------------------------------------
# TAB 1: GABUNG PDF (MERGE)
# ---------------------------------------------------------
with tab_merge:
    st.subheader("Gabungkan Beberapa File PDF")
    uploaded_pdfs = st.file_uploader(
        "Pilih file PDF (bisa lebih dari satu):",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge_uploader",
    )

    if uploaded_pdfs:
        st.write(f"Total file dipilih: **{len(uploaded_pdfs)} file**")

        if st.button("Proses Penggabungan", type="primary", key="btn_merge"):
            writer = PdfWriter()
            for pdf_file in uploaded_pdfs:
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)

            out_buf = io.BytesIO()
            writer.write(out_buf)
            merged_bytes = out_buf.getvalue()

            st.success("File PDF berhasil digabungkan!")
            st.download_button(
                label="📥 Unduh PDF Hasil Gabungan",
                data=merged_bytes,
                file_name="hasil_gabungan.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ---------------------------------------------------------
# TAB 2: PISAH / EKSTRAK HALAMAN (SPLIT)
# ---------------------------------------------------------
with tab_split:
    st.subheader("Ekstrak atau Pisahkan Halaman Tertentu")
    split_file = st.file_uploader(
        "Pilih dokumen PDF:", type=["pdf"], key="split_uploader"
    )

    if split_file:
        reader = PdfReader(split_file)
        total_pages = len(reader.pages)
        st.info(f"Dokumen memiliki total: **{total_pages} halaman**.")

        page_input = st.text_input(
            "Masukkan halaman yang ingin diekstrak (contoh: 1, 3-5):",
            placeholder="1, 3-5",
        )

        if st.button("Ekstrak Halaman", type="primary", key="btn_split"):
            if not page_input.strip():
                st.warning("Silakan masukkan nomor halaman terlebih dahulu.")
            else:
                selected_indices = set()
                try:
                    for part in page_input.split(","):
                        part = part.strip()
                        if "-" in part:
                            start, end = map(int, part.split("-"))
                            for num in range(start, end + 1):
                                if 1 <= num <= total_pages:
                                    selected_indices.add(num - 1)
                        else:
                            num = int(part)
                            if 1 <= num <= total_pages:
                                selected_indices.add(num - 1)

                    if not selected_indices:
                        st.error("Nomor halaman tidak valid atau di luar rentang.")
                    else:
                        writer = PdfWriter()
                        for idx in sorted(list(selected_indices)):
                            writer.add_page(reader.pages[idx])

                        out_buf = io.BytesIO()
                        writer.write(out_buf)
                        split_bytes = out_buf.getvalue()

                        st.success(
                            f"Berhasil mengekstrak {len(selected_indices)} halaman!"
                        )
                        st.download_button(
                            label="📥 Unduh PDF Hasil Ekstrak",
                            data=split_bytes,
                            file_name="hasil_ekstrak.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                except ValueError:
                    st.error("Format input salah. Gunakan angka dan tanda minus.")

# ---------------------------------------------------------
# TAB 3: PUTAR HALAMAN (ROTATE)
# ---------------------------------------------------------
with tab_rotate:
    st.subheader("Putar Orientasi Halaman")
    rotate_file = st.file_uploader(
        "Pilih dokumen PDF:", type=["pdf"], key="rotate_uploader"
    )

    if rotate_file:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            rotation_angle = st.selectbox(
                "Derajat Putaran (Searah Jarum Jam):",
                [90, 180, 270],
                format_func=lambda x: f"{x}°",
            )
        with col_r2:
            rotate_scope = st.radio(
                "Terapkan Pada:",
                ["Semua Halaman", "Halaman Tertentu Saja"],
                horizontal=True,
            )

        target_pages = ""
        if rotate_scope == "Halaman Tertentu Saja":
            target_pages = st.text_input(
                "Masukkan nomor halaman (contoh: 1, 3):",
                placeholder="1, 3",
            )

        if st.button("Putar Halaman", type="primary", key="btn_rotate"):
            reader = PdfReader(rotate_file)
            writer = PdfWriter()
            total_pages = len(reader.pages)

            pages_to_rotate = set()
            if rotate_scope == "Semua Halaman":
                pages_to_rotate = set(range(total_pages))
            else:
                try:
                    for part in target_pages.split(","):
                        num = int(part.strip())
                        if 1 <= num <= total_pages:
                            pages_to_rotate.add(num - 1)
                except ValueError:
                    pass

            for idx, page in enumerate(reader.pages):
                if idx in pages_to_rotate:
                    page.rotate(rotation_angle)
                writer.add_page(page)

            out_buf = io.BytesIO()
            writer.write(out_buf)
            rotated_bytes = out_buf.getvalue()

            st.success("Halaman berhasil diputar!")
            st.download_button(
                label="📥 Unduh PDF Hasil Putar",
                data=rotated_bytes,
                file_name="hasil_putar.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ---------------------------------------------------------
# TAB 4: PROTECT & UNLOCK
# ---------------------------------------------------------
with tab_protect:
    st.subheader("Kunci atau Buka Password Dokumen")
    sec_file = st.file_uploader(
        "Pilih dokumen PDF:", type=["pdf"], key="sec_uploader"
    )

    if sec_file:
        sec_mode = st.radio(
            "Pilih Operasi:",
            ["Beri Password (Encrypt)", "Buka Password (Decrypt)"],
            horizontal=True,
        )
        password = st.text_input(
            "Masukkan Password:", type="password", key="sec_pass"
        )

        if st.button("Jalankan Operasi", type="primary", key="btn_sec"):
            if not password:
                st.warning("Password wajib diisi.")
            else:
                reader = PdfReader(sec_file)
                writer = PdfWriter()

                if sec_mode == "Beri Password (Encrypt)":
                    for page in reader.pages:
                        writer.add_page(page)
                    writer.encrypt(password)

                    out_buf = io.BytesIO()
                    writer.write(out_buf)
                    st.success("PDF berhasil dienkripsi!")
                    st.download_button(
                        label="📥 Unduh PDF Terproteksi",
                        data=out_buf.getvalue(),
                        file_name="dokumen_terkunci.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    if reader.is_encrypted:
                        decrypt_status = reader.decrypt(password)
                        if decrypt_status != 0:
                            for page in reader.pages:
                                writer.add_page(page)

                            out_buf = io.BytesIO()
                            writer.write(out_buf)
                            st.success("Password berhasil dihapus dari PDF!")
                            st.download_button(
                                label="📥 Unduh PDF Tanpa Password",
                                data=out_buf.getvalue(),
                                file_name="dokumen_terbuka.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )
                        else:
                            st.error("Password salah. Dokumen gagal dibuka.")
                    else:
                        st.info("Dokumen ini tidak terkunci password.")

# ---------------------------------------------------------
# TAB 5: GAMBAR KE PDF (IMAGES TO PDF)
# ---------------------------------------------------------
with tab_img2pdf:
    st.subheader("Gabungkan Gambar (JPG/PNG) Menjadi PDF")
    uploaded_imgs = st.file_uploader(
        "Pilih gambar:",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="img_uploader",
    )

    if uploaded_imgs:
        st.write(f"Total gambar: **{len(uploaded_imgs)} file**")
        if st.button("Buat Dokumen PDF", type="primary", key="btn_img2pdf"):
            pil_images = []
            for img_file in uploaded_imgs:
                img = Image.open(img_file)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                pil_images.append(img)

            if pil_images:
                out_buf = io.BytesIO()
                first_img = pil_images[0]
                first_img.save(
                    out_buf,
                    format="PDF",
                    save_all=True,
                    append_images=pil_images[1:],
                )

                st.success("Dokumen PDF dari gambar berhasil dibuat!")
                st.download_button(
                    label="📥 Unduh Hasil PDF Gambar",
                    data=out_buf.getvalue(),
                    file_name="koleksi_gambar.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )