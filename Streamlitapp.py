import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import json

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="Gemini Data Dashboard")

# --- Function for Data Cleaning ---
def clean_data(df):
    """
    Cleans the input DataFrame:
    - Converts 'Date' column to datetime objects (YYYY-MM-DD format).
    - Fills empty 'Engagements' with 0 and converts to numeric.
    """
    # Convert 'Date' to datetime, handling potential errors
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Filter out rows where Date couldn't be parsed
    df = df.dropna(subset=['Date'])
    # Format Date to YYYY-MM-DD string for display and consistency
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    # Fill empty 'Engagements' with 0 and convert to numeric
    # Use pd.to_numeric with errors='coerce' to turn non-numeric into NaN, then fill
    df['Engagements'] = pd.to_numeric(df['Engagements'], errors='coerce').fillna(0)
    return df

# --- Gemini API Call Function ---
def get_gemini_response(prompt_text, api_key):
    """
    Calls the Gemini API to get a text response.
    """
    if not api_key:
        return "API Key tidak tersedia untuk menghasilkan insight."

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}]
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()

        if result.get("candidates") and result["candidates"][0].get("content") and \
           result["candidates"][0]["content"].get("parts") and \
           result["candidates"][0]["content"]["parts"][0].get("text"):
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "Tidak dapat menghasilkan insight. Struktur respons tidak terduga."
    except requests.exceptions.RequestException as e:
        return f"Terjadi kesalahan saat memanggil Gemini API: {e}. Pastikan API Key valid dan koneksi internet stabil."
    except json.JSONDecodeError:
        return "Terjadi kesalahan saat menguraikan respons JSON dari API."
    except Exception as e:
        return f"Terjadi kesalahan yang tidak terduga: {e}"

# --- Main App Components ---
def main():
    # --- API Key Configuration (FOR DEMONSTRATION ONLY) ---
    # In a production environment, use st.secrets or environment variables
    # For example:
    # GEMINI_API_KEY = st.secrets["gemini_api_key"]
    GEMINI_API_KEY = "AIzaSyC7SjhHIrA2VrmuYcTYFhCXR2Ffg09L2_Y" # Your API Key here

    st.markdown(
        """
        <style>
            .reportview-container .main .block-container {
                padding-top: 2rem;
                padding-right: 2rem;
                padding-left: 2rem;
                padding-bottom: 2rem;
            }
            h1 {
                color: #4A00B7; /* Deep Purple */
                text-align: center;
                font-weight: bold;
            }
            .stFileUploader label {
                font-size: 1.25rem;
                font-weight: 500;
                color: #5500B7;
            }
            .stButton>button {
                background-color: #4CAF50; /* Green for export */
                color: white;
                font-weight: bold;
                border-radius: 0.5rem;
                padding: 0.75rem 1.5rem;
            }
            .stSelectbox, .stDateInput, .stMultiSelect {
                margin-bottom: 1rem;
            }
            .filter-section {
                background-color: #F3E5F5; /* Light purple */
                padding: 1.5rem;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .summary-section {
                background-color: #E3F2FD; /* Light blue */
                padding: 1.5rem;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .chart-card {
                background-color: white;
                padding: 1.5rem;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 1.5rem;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            .insights-list {
                list-style-type: disc;
                margin-left: 1.25rem;
                font-size: 0.9rem;
                color: #4B5563;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Gemini Data Dashboard")
    st.write("Analisis data media sosial Anda dengan visualisasi interaktif.")

    group_name = "Kelompok Gemini Insight"
    st.markdown(f"<div style='text-align: center; color: #6D28D9; font-size: 1.5rem; font-weight: 600; margin-bottom: 2rem; padding: 0.75rem; border-top: 1px solid #D1C4E9; border-bottom: 1px solid #D1C4E9;'>{group_name}</div>", unsafe_allow_html=True)

    # --- File Upload Section ---
    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
    st.subheader("Unggah File CSV:")
    uploaded_file = st.file_uploader("", type="csv")
    st.markdown("</div>", unsafe_allow_html=True)

    df = pd.DataFrame()
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df = clean_data(df.copy()) # Clean data immediately after upload
            st.success("File berhasil diunggah dan data dibersihkan!")

            # --- Key Action Summary Section (Dynamic) ---
            st.markdown("<div class='summary-section' style='margin-top: 2rem;'>", unsafe_allow_html=True)
            st.subheader("Ringkasan Strategi Kampanye (Key Action Summary)")

            # Generate dynamic summary only if data is available
            if not df.empty:
                summary_prompt = f"""
                Berdasarkan data sosial media berikut (hanya 5 baris pertama untuk contoh):
                {df.head().to_string()}
                dan kolom yang tersedia: {df.columns.tolist()}.
                Tuliskan ringkasan strategi kampanye yang relevan dan singkat (sekitar 3-5 poin kunci) dalam bahasa Indonesia,
                fokus pada engagement, sentimen, platform, media type, dan lokasi.
                """
                with st.spinner("Menghasilkan ringkasan strategi kampanye..."):
                    campaign_summary = get_gemini_response(summary_prompt, GEMINI_API_KEY)
                    st.markdown(campaign_summary)
            else:
                st.markdown("Silakan unggah data untuk menghasilkan ringkasan strategi kampanye.")
            st.markdown("</div>", unsafe_allow_html=True)

            # --- Filters Section ---
            st.markdown("<div class='filter-section' style='margin-top: 2rem;'>", unsafe_allow_html=True)
            st.subheader("Saring Data")

            col1, col2, col3 = st.columns(3)
            with col1:
                platforms = ['All'] + sorted(df['Platform'].unique().tolist()) if 'Platform' in df.columns else ['All']
                selected_platform = st.selectbox("Platform:", platforms)
            with col2:
                sentiments = ['All'] + sorted(df['Sentiment'].unique().tolist()) if 'Sentiment' in df.columns else ['All']
                selected_sentiment = st.selectbox("Sentimen:", sentiments)
            with col3:
                media_types = ['All'] + sorted(df['Media Type'].unique().tolist()) if 'Media Type' in df.columns else ['All']
                selected_media_type = st.selectbox("Jenis Media:", media_types)

            col4, col5, col6 = st.columns(3)
            with col4:
                locations = ['All'] + sorted(df['Location'].unique().tolist()) if 'Location' in df.columns else ['All']
                selected_location = st.selectbox("Lokasi:", locations)
            with col5:
                # Convert 'Date' back to datetime for date filtering
                df_for_date_filter = df.copy()
                df_for_date_filter['Date'] = pd.to_datetime(df_for_date_filter['Date'])
                min_date = df_for_date_filter['Date'].min().date() if not df_for_date_filter.empty else pd.to_datetime('2000-01-01').date()
                max_date = df_for_date_filter['Date'].max().date() if not df_for_date_filter.empty else pd.to_datetime('2030-12-31').date()

                start_date = st.date_input("Tanggal Mulai:", min_value=min_date, max_value=max_date, value=min_date)
            with col6:
                end_date = st.date_input("Tanggal Berakhir:", min_value=min_date, max_value=max_date, value=max_date)

            filtered_df = df.copy()

            if selected_platform != 'All':
                filtered_df = filtered_df[filtered_df['Platform'] == selected_platform]
            if selected_sentiment != 'All':
                filtered_df = filtered_df[filtered_df['Sentiment'] == selected_sentiment]
            if selected_media_type != 'All':
                filtered_df = filtered_df[filtered_df['Media Type'] == selected_media_type]
            if selected_location != 'All':
                filtered_df = filtered_df[filtered_df['Location'] == selected_location]

            # Date filtering
            filtered_df['Date_dt'] = pd.to_datetime(filtered_df['Date'])
            if start_date:
                filtered_df = filtered_df[filtered_df['Date_dt'] >= pd.to_datetime(start_date)]
            if end_date:
                filtered_df = filtered_df[filtered_df['Date_dt'] <= pd.to_datetime(end_date)]
            filtered_df = filtered_df.drop(columns=['Date_dt']) # Drop temporary column

            st.markdown("</div>", unsafe_allow_html=True) # End filter-section

            if filtered_df.empty:
                st.warning("Tidak ada data yang cocok dengan filter yang dipilih.")
                return

            # --- Visualizations Section ---
            st.subheader("Visualisasi Data")
            col_chart1, col_chart2 = st.columns(2)

            # 1. Pie Chart: Sentiment Breakdown
            with col_chart1:
                st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
                sentiment_counts = filtered_df['Sentiment'].value_counts().reset_index()
                sentiment_counts.columns = ['Sentiment', 'Count']
                fig_sentiment = px.pie(sentiment_counts, values='Count', names='Sentiment',
                                       title='Sentiment Breakdown', hole=0.4,
                                       color_discrete_sequence=px.colors.qualitative.Plotly)
                fig_sentiment.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_sentiment, use_container_width=True)

                st.markdown("### Insight:")
                insight_prompt = f"""
                Berdasarkan data sentimen berikut (sentimen: jumlah): {sentiment_counts.to_string()}.
                Berikan 3 insight singkat dan relevan tentang sentimen ini dalam bahasa Indonesia.
                """
                with st.spinner("Menghasilkan insight sentimen..."):
                    sentiment_insights = get_gemini_response(insight_prompt, GEMINI_API_KEY)
                    st.markdown(sentiment_insights)
                st.markdown("</div>", unsafe_allow_html=True)

            # 2. Line Chart: Engagement Trend over Time
            with col_chart2:
                st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
                df_engagement_trend = filtered_df.copy()
                df_engagement_trend['Date_dt'] = pd.to_datetime(df_engagement_trend['Date'])
                engagement_by_date = df_engagement_trend.groupby('Date_dt')['Engagements'].sum().reset_index()
                engagement_by_date = engagement_by_date.sort_values('Date_dt')

                fig_engagement = px.line(engagement_by_date, x='Date_dt', y='Engagements',
                                         title='Engagement Trend over Time')
                fig_engagement.update_xaxes(title_text='Date')
                fig_engagement.update_yaxes(title_text='Total Engagements')
                st.plotly_chart(fig_engagement, use_container_width=True)

                st.markdown("### Insight:")
                insight_prompt = f"""
                Berdasarkan tren engagement berikut (tanggal: engagement): {engagement_by_date.to_string()}.
                Berikan 3 insight singkat dan relevan tentang tren engagement ini dalam bahasa Indonesia.
                """
                with st.spinner("Menghasilkan insight tren engagement..."):
                    engagement_insights = get_gemini_response(insight_prompt, GEMINI_API_KEY)
                    st.markdown(engagement_insights)
                st.markdown("</div>", unsafe_allow_html=True)

            col_chart3, col_chart4 = st.columns(2)

            # 3. Bar Chart: Platform Engagements
            with col_chart3:
                st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
                platform_engagements = filtered_df.groupby('Platform')['Engagements'].sum().reset_index()
                fig_platform = px.bar(platform_engagements, x='Platform', y='Engagements',
                                      title='Platform Engagements',
                                      color_discrete_sequence=px.colors.qualitative.Safe)
                fig_platform.update_xaxes(title_text='Platform')
                fig_platform.update_yaxes(title_text='Total Engagements')
                st.plotly_chart(fig_platform, use_container_width=True)

                st.markdown("### Insight:")
                insight_prompt = f"""
                Berdasarkan engagement platform berikut (platform: engagement): {platform_engagements.to_string()}.
                Berikan 3 insight singkat dan relevan tentang engagement platform ini dalam bahasa Indonesia.
                """
                with st.spinner("Menghasilkan insight platform engagement..."):
                    platform_insights = get_gemini_response(insight_prompt, GEMINI_API_KEY)
                    st.markdown(platform_insights)
                st.markdown("</div>", unsafe_allow_html=True)

            # 4. Pie Chart: Media Type Mix
            with col_chart4:
                st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
                media_type_counts = filtered_df['Media Type'].value_counts().reset_index()
                media_type_counts.columns = ['Media Type', 'Count']
                fig_media_type = px.pie(media_type_counts, values='Count', names='Media Type',
                                        title='Media Type Mix', hole=0.4,
                                        color_discrete_sequence=px.colors.qualitative.Vivid)
                fig_media_type.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_media_type, use_container_width=True)

                st.markdown("### Insight:")
                insight_prompt = f"""
                Berdasarkan jenis media berikut (jenis media: jumlah): {media_type_counts.to_string()}.
                Berikan 3 insight singkat dan relevan tentang jenis media ini dalam bahasa Indonesia.
                """
                with st.spinner("Menghasilkan insight jenis media..."):
                    media_type_insights = get_gemini_response(insight_prompt, GEMINI_API_KEY)
                    st.markdown(media_type_insights)
                st.markdown("</div>", unsafe_allow_html=True)

            # 5. Bar Chart: Top 5 Locations
            st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
            location_counts = filtered_df['Location'].value_counts().nlargest(5).reset_index()
            location_counts.columns = ['Location', 'Count']
            fig_location = px.bar(location_counts, x='Location', y='Count',
                                  title='Top 5 Locations',
                                  color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_location.update_xaxes(title_text='Location')
            fig_location.update_yaxes(title_text='Number of Posts')
            st.plotly_chart(fig_location, use_container_width=True)

            st.markdown("### Insight:")
            insight_prompt = f"""
            Berdasarkan 5 lokasi teratas berikut (lokasi: jumlah): {location_counts.to_string()}.
            Berikan 3 insight singkat dan relevan tentang lokasi ini dalam bahasa Indonesia.
            """
            with st.spinner("Menghasilkan insight lokasi..."):
                location_insights = get_gemini_response(insight_prompt, GEMINI_API_KEY)
                st.markdown(location_insights)
            st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses file: {e}")
            st.info("Harap pastikan file CSV Anda memiliki kolom seperti: 'Date', 'Engagements', 'Platform', 'Sentiment', 'Media Type', 'Location'.")

# Run the app
if __name__ == "__main__":
    main()
