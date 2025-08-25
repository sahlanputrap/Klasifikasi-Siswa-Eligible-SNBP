import pickle
import streamlit as st
from PIL import Image
import numpy as np
import base64
from io import BytesIO
import pandas as pd

eligible_model = pickle.load(open('model_eligible.sav', 'rb'))

gambar = Image.open('logo_unikom_kuning.png')
buffered = BytesIO()
gambar.save(buffered, format="PNG")
img_str = base64.b64encode(buffered.getvalue()).decode()

st.markdown(
    """
    <style>
    .center {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .center-title {
        text-align: center;
        color: #1E3A8A;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .result-box {
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
        margin-bottom: 15px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
    }
    .eligible {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #22C55E;
    }
    .not-eligible {
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #EF4444;
    }
    .description {
        font-size: 16px;
        text-align: center;
        color: #555;
        margin-top: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

menu = ['Home', 'Probabilitas Siswa Eligible', 'Prediksi Siswa Eligible']
selected_menu = st.sidebar.selectbox('MENU', menu)

st.markdown(f'<div class="center"><img src="data:image/png;base64,{img_str}" width="180"></div>', unsafe_allow_html=True)
st.markdown('<h2 class="center-title">Universitas Komputer Indonesia</h2>', unsafe_allow_html=True)

def tingkat_prestasi(prestasi):
    mapping = {
        'Tidak Ada': 0, 'KOTA': 1, 'PROVINSI': 2, 'NASIONAL': 3, 'INTERNASIONAL': 4
    }
    return mapping.get(prestasi, None)

def kategori_juara(kategori):
    mapping = {
        'Tidak Ada': 0, 'JUARA HARAPAN 2': 1, 'JUARA HARAPAN 1': 2,
        'JUARA 3': 3, 'JUARA 2': 4, 'JUARA 1': 5
    }
    return mapping.get(kategori, None)


if selected_menu == 'Home':
    st.markdown('<h2 class="center-title">Selamat Datang</h2>', unsafe_allow_html=True)
    st.markdown('<div class="description">Gunakan menu di sebelah kiri untuk memulai prediksi dan rekomendasi jurusan.</div>', unsafe_allow_html=True)

elif selected_menu == 'Probabilitas Siswa Eligible':
    st.markdown('<h2 class="center-title">Probabilitas Siswa Eligible</h2>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload file (CSV/Excel)", type=["csv", "xlsx"])

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file)
        else:
            data = pd.read_excel(uploaded_file, engine='openpyxl')

        st.write("Data yang diunggah:", data)

        if st.button('Prediksi'):
            try:
                data['TINGKAT_PRESTASI_NON_AKADEMIK'] = data['TINGKAT_PRESTASI_NON_AKADEMIK'].apply(tingkat_prestasi)
                data['KATEGORI_JUARA'] = data['KATEGORI_JUARA'].apply(kategori_juara)

                data['KONSISTENSI_SD'] = data[['SEM1','SEM2','SEM3','SEM4','SEM5']].std(axis=1)
                max_std = data['KONSISTENSI_SD'].max()
                data['SKOR_KONSISTENSI'] = (1 - (data['KONSISTENSI_SD'] / max_std)) * 100

                beasprediction = eligible_model.predict(data[['RATA-RATA', 'TINGKAT_PRESTASI_NON_AKADEMIK', 'KATEGORI_JUARA', 'SKOR_KONSISTENSI']])
                beasproba = eligible_model.predict_proba(data[['RATA-RATA', 'TINGKAT_PRESTASI_NON_AKADEMIK', 'KATEGORI_JUARA', 'SKOR_KONSISTENSI']])

                data['Hasil Prediksi'] = ['Eligible' if pred == 1 else 'Tidak Eligible' for pred in beasprediction]
                data['Probabilitas Eligible'] = beasproba[:, 1]
                data['Probabilitas Tidak Eligible'] = beasproba[:, 0]

                st.success("Prediksi berhasil dilakukan!")
                st.dataframe(data)

            except Exception as e:
                st.error(f"Terjadi kesalahan: {str(e)}")


# --- MENU PREDIKSI ELIGIBLE ---
elif selected_menu == 'Prediksi Siswa Eligible':
    st.markdown('<h2 class="center-title">Prediksi Siswa Eligible</h2>', unsafe_allow_html=True)

    semester_values = {}
    valid_input = True

    # Layout kolom input
    cols = st.columns(5)
    for i, col in enumerate(cols, 1):
        val = col.text_input(f'Semester {i}', key=f'sem{i}')
        try:
            val = float(val)
            if 0 <= val <= 100:
                semester_values[f'SEM{i}'] = val
            else:
                col.error('0 - 100')
                valid_input = False
        except:
            if val != '':
                col.error('Harus angka')
                valid_input = False 

    RATA = None
    SKOR_KONSISTENSI = None

    if valid_input and len(semester_values) == 5:
        RATA = sum(semester_values.values()) / 5
        konsistensi_sd = pd.Series(list(semester_values.values())).std()
        max_std = 5.567397809331301
        SKOR_KONSISTENSI = (1 - (konsistensi_sd / max_std)) * 100

        st.info(f'RATA-RATA: **{RATA:.2f}**')
        st.info(f'SKOR KONSISTENSI: **{SKOR_KONSISTENSI:.2f}**')

    Tingkat_Prestasi = st.selectbox('Tingkat Prestasi Non Akademik', ['Tidak Ada', 'KOTA', 'PROVINSI', 'NASIONAL', 'INTERNASIONAL'])
    Kategori_Juara = st.selectbox('Kategori Juara', ['Tidak Ada', 'JUARA HARAPAN 2', 'JUARA HARAPAN 1', 'JUARA 3', 'JUARA 2', 'JUARA 1'])

    if st.button('Prediksi'):
        if RATA is None or SKOR_KONSISTENSI is None:
            st.error("Input belum lengkap")
        else:
            Tingkat_Prestasi_num = tingkat_prestasi(Tingkat_Prestasi)
            Kategori_Juara_num = kategori_juara(Kategori_Juara)

            input_array = np.array([[RATA, SKOR_KONSISTENSI, Tingkat_Prestasi_num, Kategori_Juara_num]])
            beasprediction = eligible_model.predict(input_array)
            beasproba = eligible_model.predict_proba(input_array)

            hasil_prediksi = 'Eligible' if beasprediction[0] == 1 else 'Tidak Eligible'
            prob_eligible = beasproba[0][1]
            prob_tidak = beasproba[0][0]

            st.write(f"Probabilitas Eligible: **{prob_eligible:.2f}**")
            st.write(f"Probabilitas Tidak Eligible: **{prob_tidak:.2f}**")

            if hasil_prediksi == "Eligible":
                st.markdown(f'<div class="result-box eligible">Hasil Prediksi: {hasil_prediksi}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="result-box not-eligible">Hasil Prediksi: {hasil_prediksi}</div>', unsafe_allow_html=True)