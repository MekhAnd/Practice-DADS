# MAGIST PROJECT

* ### School
* ### Instructors
* ### Legend
* ### Team
* ### Table of Slides
* ### Notebook
* ### List of Tools and Technologies


## School:
    
__WBS Web Coding School__

## Instructors
* Marlo Paßler


## Legend:
Moosic is a little start-up that creates playlists curated by music experts and specialists in old and new trends. Users can subscribe to their website and listen to these playlists through their preferred Music App (be it Spotify, Apple Music, Youtube Music…). 

Business is scaling up fast and the music experts are slow in creating new playlists. They have hired you with a clear mission: use Data Science to add a degree of automatisation to the creation of playlists.

They want you to use a dataset that has been collected from the Spotify API and contains the audio features (tempo, energy, danceability…) for a few thousand songs and use a basic clustering algorithm such as K-Means to divide the dataset into a few clusters (which will become playlists).

__Are Spotify’s audio features able to identify “similar songs”, as defined by humanly detectable criteria?__ When you listen to two rock ballads, two operas or two drum & bass songs, you identify them as similar songs. Are these similarities detectable using the audio features from Spotify?
__Is K-Means a good method to create playlists?__ Would you stick with this algorithm moving forward, or explore other methods to create playlists?

## Team
* Lucky Nguyen
* Andrii Mekhanich

## Table of Slides

1. __Title__
2. __THE LOGIC OF OUR CONCLUSIONS__

Overview of technologies, and project logic.

3. __SHORT INTRODUCTIONS TO CONCLUSIONS__


4. __PLAYLISTS EXAMPLES__

Two playlists that were distributed using the KMeans algorithm with certain parameters (n_clusters=54, PCA= 0.93)

__Highlights:__
 - Using only audio parameters does not allow for a qualitative distribution of the data set into separate playlists.
 - At this stage, the process is more similar to a random distribution than a correct distribution

5. __PLAYLISTS EXAMPLES__

Displaying genre distribution in playlists

__Highlights:__
- Playlist #1 shows 12 distinct genres, with three dominant categories (POP, Rock, Metal), while the second playlist contains only 6 genres, with a single dominant one.

6. __PLAYLISTS EXAMPLES__

Displaying genre distribution in playlists (3 playlists, n_clusters = 146, PCA(0.9324643658582555))

7. __CONCLUSIONS AND RECOMMENDATIONS__
8. __ANNEXES__
- Charts

## Notebook
You can find [notebook here](https://github.com/MekhAnd/Practice-DADS/blob/main/WBSCodingSchool/ML/Unsupervised%20learning/MLI_diff_clusters_500.ipynb)

## List of Tools and Technologies
Python, sklearn (KMeans), seaborn, plotly, matplotlib


