import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Cage Match[er]",
    layout="wide"
)

def init_supabase():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    return create_client(supabase_url, supabase_key)

def main():
    st.image("https://cdn1.sbnation.com/assets/3430219/ExtremeBliss.gif", 
                 width=400)
    
    # Centered title and subheading
    st.markdown("<h1 style='text-align: center; font-size: 3.5em;'>Cage Match[er]</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Pick a genre, any genre. Nic Cage has probably done something in it. With this tool you can see which ones are his best!</h3>", unsafe_allow_html=True)
    
    supabase = init_supabase()
    
    response = supabase.table("nicholas_cage_movies").select("*").order("imdb_rank").execute()
    df = pd.DataFrame(response.data)
    
    st.sidebar.header("Filters")
    min_rating = st.sidebar.slider("Minimum Rating", 0.0, 10.0, 0.0, 0.1)
    
    all_genres = set()
    for genres in df['genres']:
        if genres:
            all_genres.update(genres)
    
    selected_genres = st.sidebar.multiselect("Genres", sorted(all_genres))
    
    filtered_df = df[df['imdb_rating'] >= min_rating]
    if selected_genres:
        filtered_df = filtered_df[filtered_df['genres'].apply(
            lambda x: any(genre in x for genre in selected_genres) if x else False
        )]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ratings Distribution")
        fig_hist = px.histogram(
            filtered_df, 
            x='imdb_rating', 
            nbins=20,
            color_discrete_sequence=['#FF4B4B']
        )
        fig_hist.update_traces(
            marker=dict(
                line=dict(width=2, color='DarkSlateGrey')
            )
        )
        fig_hist.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with col2:
        st.subheader("Top Rated Movies")
        top_movies = filtered_df.nlargest(106, 'imdb_rating')[['title', 'imdb_rating', 'genres']]
        
        # Make the dataframe scrollable with fixed height
        st.dataframe(
            top_movies, 
            use_container_width=True,
            height=400  # Fixed height makes it scrollable
        )
    
    st.subheader("Movies by Genre")
    genre_counts = {}
    for genres in filtered_df['genres']:
        if genres:
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    genre_df = pd.DataFrame(list(genre_counts.items()), columns=['Genre', 'Count'])
    fig_pie = px.pie(
        genre_df, 
        values='Count', 
        names='Genre',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig_pie, use_container_width=True)

if __name__ == "__main__":
    main()