import io
import os
import tempfile
import zipfile
from pdf2docx import Converter
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
import streamlit as st
import fitz  # PyMuPDF

st.set_page_config(
    page_title="PDFku by LYD Bali Group",
    page_icon="📑",
    layout="wide",
)

st.title("📑 PDF Swiss Knife Pro")
st.caption(
    "Aplikasi manipulasi PDF."
)


# Helper: Membuat watermark transparan menggunakan ReportLab
def generate_watermark_layer(text, width, height, opacity=0.3):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    # Warna abu-abu dengan transparansi alpha
    can.setFillColor(Color(0.5, 0.5, 0.5, alpha=opacity))
    can.setFont("Helvetica-Bold", 45)
    can.saveState()
    # Pindahkan origin ke tengah dan putar 45 derajat
    can.translate(width / 2.0, height / 2.0)
    can.rotate(45)
    can.drawCentredString(0, 0, text)
    can.restoreState()
    can.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]


# Navigasi Tab Lengkap
(
    tab_merge,
    tab_split,
    tab_rotate,
    tab_compress,
    tab_watermark,
    tab_protect,
    tab_extract,
    tab_img2pdf,
    tab_pdf2docx,
    tab_edit_text
) = st.tabs(
    [
        "🔗 Gabung",
        "✂️ Pisah",
        "🔄 Putar",
        "🗜️ Kompres",
        "🏷️ Watermark",
        "🔒 Keamanan",
        "📦 Ekstrak Aset",
        "🖼️ Gambar ke PDF",
        "📝 PDF ke Word",
        "✏️ Edit Teks"
    ]
)

# ---------------------------------------------------------
# TAB 1: GABUNG PDF (MERGE)
# ---------------------------------------------------------
with tab_merge:
    st.subheader("Gabungkan Beberapa File PDF")
    uploaded_pdfs = st.file_uploader(
        "Pilih file PDF:",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge_uploader",
    )

    if uploaded_pdfs:
        st.write(f"Total file dipilih: **{len(uploaded_pdfs)} file**")
        if st.button("Gabungkan Dokumen", type="primary", key="btn_merge"):
            writer = PdfWriter()
            for pdf_file in uploaded_pdfs:
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)

            out_buf = io.BytesIO()
            writer.write(out_buf)

            st.success("File PDF berhasil digabungkan!")
            st.download_button(
                label="📥 Unduh PDF Hasil Gabungan",
                data=out_buf.getvalue(),
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
                        st.error(
                            "Nomor halaman tidak valid atau di luar jangkauan."
                        )
                    else:
                        writer = PdfWriter()
                        for idx in sorted(list(selected_indices)):
                            writer.add_page(reader.pages[idx])

                        out_buf = io.BytesIO()
                        writer.write(out_buf)

                        st.success(
                            f"Berhasil mengekstrak {len(selected_indices)} halaman!"
                        )
                        st.download_button(
                            label="📥 Unduh PDF Hasil Ekstrak",
                            data=out_buf.getvalue(),
                            file_name="hasil_ekstrak.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                except ValueError:
                    st.error(
                        "Format input salah. Gunakan angka dan tanda hubung minus (-)."
                    )

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
                "Masukkan nomor halaman (contoh: 1, 3):", placeholder="1, 3"
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

            st.success("Halaman berhasil diputar!")
            st.download_button(
                label="📥 Unduh PDF Hasil Putar",
                data=out_buf.getvalue(),
                file_name="hasil_putar.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ---------------------------------------------------------
# TAB 4: KOMPRESI PDF (COMPRESS)
# ---------------------------------------------------------
with tab_compress:
    st.subheader("Perkecil Ukuran File PDF")
    compress_file = st.file_uploader(
        "Pilih file PDF yang ingin dikompresi:",
        type=["pdf"],
        key="compress_uploader",
    )

    if compress_file:
        orig_size = len(compress_file.getvalue()) / 1024
        st.write(f"Ukuran asli: **{orig_size:.2f} KB**")

        quality_slider = st.slider(
            "Kualitas Kompresi Gambar Internal (Skala):",
            min_value=20,
            max_value=90,
            value=60,
            help="Semakin kecil nilai, ukuran file makin ramping namun ketajaman gambar menurun.",
        )

        if st.button("Kompres Dokumen", type="primary", key="btn_compress"):
            reader = PdfReader(compress_file)
            writer = PdfWriter()

            for page in reader.pages:
                page.compress_content_streams()
                writer.add_page(page)

            for page in writer.pages:
                for img in page.images:
                    img.replace(img.image, quality=quality_slider)

            out_buf = io.BytesIO()
            writer.write(out_buf)
            comp_bytes = out_buf.getvalue()
            new_size = len(comp_bytes) / 1024

            st.success(
                f"Ukuran berhasil dikurangi dari {orig_size:.2f} KB menjadi {new_size:.2f} KB!"
            )
            st.download_button(
                label="📥 Unduh PDF Hasil Kompres",
                data=comp_bytes,
                file_name="hasil_kompres.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ---------------------------------------------------------
# TAB 5: WATERMARK TEKS DINAMIS
# ---------------------------------------------------------
with tab_watermark:
    st.subheader("Beri Watermark Teks Dinamis")
    wm_file = st.file_uploader(
        "Pilih file PDF:", type=["pdf"], key="wm_uploader"
    )

    if wm_file:
        col_wm1, col_wm2 = st.columns(2)
        with col_wm1:
            wm_text = st.text_input(
                "Teks Watermark:",
                placeholder="CONTOH: DOKUMEN RAHASIA",
                value="CONFIDENTIAL",
            )
        with col_wm2:
            wm_opacity = st.slider(
                "Transparansi Watermark:",
                min_value=0.1,
                max_value=1.0,
                value=0.25,
                step=0.05,
            )

        if st.button("Terapkan Watermark", type="primary", key="btn_wm"):
            reader = PdfReader(wm_file)
            writer = PdfWriter()

            for page in reader.pages:
                p_width = float(page.mediabox.width)
                p_height = float(page.mediabox.height)
                wm_page = generate_watermark_layer(
                    wm_text, p_width, p_height, opacity=wm_opacity
                )
                page.merge_page(wm_page)
                writer.add_page(page)

            out_buf = io.BytesIO()
            writer.write(out_buf)

            st.success("Watermark berhasil ditempelkan di setiap halaman!")
            st.download_button(
                label="📥 Unduh PDF dengan Watermark",
                data=out_buf.getvalue(),
                file_name="dokumen_watermark.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ---------------------------------------------------------
# TAB 6: KEAMANAN (PROTECT & UNLOCK)
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
# TAB 7: EKSTRAKSI ASET (TEKS & GAMBAR)
# ---------------------------------------------------------
with tab_extract:
    st.subheader("Ekstrak Teks dan Gambar Dokumen")
    ext_file = st.file_uploader(
        "Pilih file PDF:", type=["pdf"], key="ext_uploader"
    )

    if ext_file:
        ext_choice = st.radio(
            "Pilih Target Ekstraksi:",
            ["Semua Teks (.txt)", "Semua Gambar (.zip)"],
            horizontal=True,
        )

        if st.button("Mulai Ekstraksi", type="primary", key="btn_ext"):
            reader = PdfReader(ext_file)

            if ext_choice == "Semua Teks (.txt)":
                full_text = ""
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    full_text += (
                        f"--- [Halaman {idx + 1}] ---\n{text}\n\n"
                    )

                st.success("Teks berhasil diekstrak!")
                st.download_button(
                    label="📥 Unduh File Teks (.txt)",
                    data=full_text.encode("utf-8"),
                    file_name="hasil_ekstraksi_teks.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                zip_buffer = io.BytesIO()
                total_imgs = 0
                with zipfile.ZipFile(
                    zip_buffer, "w", zipfile.ZIP_DEFLATED
                ) as zip_file:
                    for p_idx, page in enumerate(reader.pages):
                        for img_idx, img in enumerate(page.images):
                            total_imgs += 1
                            zip_file.writestr(
                                f"hal_{p_idx + 1}_img_{img_idx + 1}_{img.name}",
                                img.data,
                            )

                if total_imgs == 0:
                    st.warning("Tidak ditemukan file gambar pada dokumen ini.")
                else:
                    st.success(
                        f"Ditemukan dan diekstrak total **{total_imgs} gambar**!"
                    )
                    st.download_button(
                        label="📥 Unduh Koleksi Gambar (.zip)",
                        data=zip_buffer.getvalue(),
                        file_name="gambar_pdf.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )

# ---------------------------------------------------------
# TAB 8: GAMBAR KE PDF (IMAGES TO PDF)
# ---------------------------------------------------------
with tab_img2pdf:
    st.subheader("Gabungkan Gambar Menjadi Satu Dokumen PDF")
    uploaded_imgs = st.file_uploader(
        "Pilih gambar (JPG / PNG):",
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

                st.success("Dokumen PDF dari koleksi gambar berhasil dibuat!")
                st.download_button(
                    label="📥 Unduh Hasil PDF",
                    data=out_buf.getvalue(),
                    file_name="koleksi_gambar.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

# Tambahkan tab baru: tab_edit_text
with tab_edit_text:
    st.subheader("✏️ Edit / Ganti Teks Langsung di PDF")
    st.caption(
        "Mencari teks target, menghapusnya, dan menuliskan teks pengganti tepat di posisi yang sama."
    )

    edit_file = st.file_uploader(
        "Pilih file PDF yang ingin diedit:", type=["pdf"], key="edit_uploader"
    )

    if edit_file:
        doc = fitz.open(stream=edit_file.getvalue(), filetype="pdf")
        total_pages = len(doc)

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            target_page_num = st.number_input(
                "Pilih Halaman:",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1,
            )
        with col_e2:
            font_size = st.number_input(
                "Ukuran Font Baru (pt):", min_value=6, max_value=72, value=11
            )

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            old_text = st.text_input(
                "Teks yang ingin diganti (Case-sensitive):",
                placeholder="Contoh: Rp 50.000",
            )
        with col_t2:
            new_text = st.text_input(
                "Teks pengganti:", placeholder="Contoh: Rp 75.000"
            )

        # Preview halaman sebelum diedit
        page = doc[target_page_num - 1]
        pix = page.get_pixmap(dpi=150)
        st.image(
            pix.tobytes("png"),
            caption=f"Pratinjau Halaman {target_page_num}",
            width=500,
        )

        if st.button("Terapkan Perubahan", type="primary", key="btn_apply_edit"):
            if not old_text:
                st.warning("Masukkan teks yang ingin dicari.")
            else:
                # Cari area persegi koordinat (bounding box) teks lama
                text_instances = page.search_for(old_text)

                if not text_instances:
                    st.error(
                        f"Teks '{old_text}' tidak ditemukan di halaman {target_page_num}."
                    )
                else:
                    for inst in text_instances:
                        # 1. Hapus/tutupi teks lama menggunakan redaction anotasi (warna putih)
                        page.add_redact_annot(inst, fill=(1, 1, 1))
                    page.apply_redactions()

                    # 2. Tulis teks baru pada posisi koordinat awal teks lama
                    for inst in text_instances:
                        # Naikkan koordinat y sedikit untuk baseline teks
                        point = fitz.Point(inst.x0, inst.y1 - 2)
                        page.insert_text(
                            point,
                            new_text,
                            fontsize=font_size,
                            color=(0, 0, 0),  # Warna teks hitam
                        )

                    # Simpan hasil ke byte array
                    edited_pdf_bytes = doc.write()

                    st.success(
                        f"Berhasil mengganti {len(text_instances)} kata '{old_text}'!"
                    )
                    st.download_button(
                        label="📥 Unduh PDF Hasil Edit",
                        data=edited_pdf_bytes,
                        file_name="hasil_edit_teks.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

# ---------------------------------------------------------
# TAB 9: PDF KE WORD (.DOCX)
# ---------------------------------------------------------
with tab_pdf2docx:
    st.subheader("Konversi Dokumen PDF ke Format Word (.docx)")
    docx_file = st.file_uploader(
        "Pilih file PDF yang ingin dikonversi:",
        type=["pdf"],
        key="pdf2docx_uploader",
    )

    if docx_file:
        if st.button("Konversi ke Word", type="primary", key="btn_pdf2docx"):
            with st.spinner("Mengonversi teks, layout, dan tabel..."):
                with tempfile.TemporaryDirectory() as temp_dir:
                    input_path = os.path.join(temp_dir, "input.pdf")
                    output_path = os.path.join(temp_dir, "output.docx")

                    with open(input_path, "wb") as f:
                        f.write(docx_file.getvalue())

                    cv = Converter(input_path)
                    cv.convert(output_path, start=0, end=None)
                    cv.close()

                    with open(output_path, "rb") as f:
                        docx_bytes = f.read()

                st.success("Konversi ke Word berhasil!")
                st.download_button(
                    label="📥 Unduh Dokumen Word (.docx)",
                    data=docx_bytes,
                    file_name="hasil_konversi.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )