# Manga Recs

## (INFO/CS 4300 - Cornell University) Language and Information Final Project

Check out our project [here](https://manga-recs.herokuapp.com/).

Manga Recs is a project that recommends mangas (Japanese comic books) based on user-inputted similar mangas and keywords to query on. Users can log in and favorite certain mangas, which is an added UX bonus as users will have a personalized experience being able to arrange their favorite set of mangas. Furthermore, users can click on a certain manga title and see a detailed view of the manga, which includes the synopsis, as well as reviews given by actual users on [MyAnimeList](https://myanimelist.net/). The project makes use of the language retrieval, NLP, and other machine learning algorithms we learned in class.

The concepts learned in class that were used are: modified Jaccard similarity, basic text processing, vector space models, TF-IDF weighting, query expansion, word embeddings. The modified Jaccard similarity and TF-IDF weighting algorithms were used to measure similarity, and word embeddings were used to make sure that if similar keywords are inputted, similar results show up. We added a little bonus UI component where every matched query keyword is highlighed in yellow, and every matched similar keyword (through word embeddings) is highlighted in green.

![home page](/img/0.png)
Our web app's home page.

![query output example 2](/img/1.png)
A query output. As shown above, word embeddings returns similar keywords to us.

![query output example 2](/img/2.png)
The same query output, but scrolled down. As shown, matched words are colorcoded.

![more details example](/img/3.png)
An example of what you would see if you clicked on a certain manga (i.e. it would show you the manga's synopsis and user reviews of it).

![login page](/img/4.png)
Our login page.
