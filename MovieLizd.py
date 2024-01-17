import tkinter as tk
from PIL import ImageTk, Image
import requests
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import random

#api key
TMDB_API_KEY = "bd594712da60f7589d4fec58ccb34acd"

#global variables for widgets
canvas = None
output_text = None
next_button = None
prev_button = None

def get_popular_movies():
    #fetches popular movies from TMDb API
    url = "https://api.themoviedb.org/3/movie/popular"
    params = {"api_key": TMDB_API_KEY, "language": "en-US", "page": 1}
    response = requests.get(url, params=params)
    data = response.json()
    movies = data.get("results", [])
    random.shuffle(movies)  #shuffles the movies to get a random order
    return movies

def home_page():
    home_frame = tk.Frame(main_frame, bg="#232323")

    #gets popular movies
    popular_movies = get_popular_movies()

    #creates 8 canvases arranged in 2 rows and 4 columns
    canvases = []
    title_labels = []  #list to store title labels

    #creates a frame for the header
    header_frame = tk.Frame(home_frame, bg="#232323")
    header_frame.pack(side=tk.TOP, fill=tk.X)

    #adds "Popular Movies" label to the header
    lb = tk.Label(header_frame, text="Popular Movies", bg="#232323", fg="white", font=("Montserrat", 25, "bold"))
    lb.pack(side=tk.LEFT, pady=(10, 20), padx=(5, 0))

    #adds "Generate Random" button to the header
    generate_button = tk.Button(header_frame, text="Generate Random", command=lambda: generate_random_movies(canvases, title_labels), font=("Montserrat", 12, "bold"), bg="#363636", fg="#c3c3c3")
    generate_button.pack(side=tk.RIGHT, pady=20, padx=(0, 5))

    for i in range(2):
        row_frame = tk.Frame(home_frame, bg="#232323")
        row_frame.pack(side=tk.TOP)

        for j in range(4):
            canvas = tk.Canvas(row_frame, width=125, height=187, bg="#363636")
            canvas.grid(row=0, column=j, padx=10, pady=10)

            #displays movie poster on the canvas
            if popular_movies:
                movie = popular_movies[i * 4 + j]
                poster_url = f"https://image.tmdb.org/t/p/w500/{movie.get('poster_path', '')}"
                response = requests.get(poster_url)
                img_data = Image.open(BytesIO(response.content))
                img_data.thumbnail((140, 190))

                img = ImageTk.PhotoImage(img_data)
                canvas.create_image(0, 0, anchor=tk.NW, image=img)
                canvas.image = img

            #add label for movie title
            title_label = tk.Label(row_frame, text=truncate_title(movie.get("title", "")), fg="white", bg="#232323", font=("Montserrat", 10))
            title_label.grid(row=1, column=j, pady=(5, 0))

            canvases.append(canvas)
            title_labels.append(title_label)  #append the title label to the list

    home_frame.pack(padx=20)

def generate_random_movies(canvases, title_labels):
    #get new random movies
    random_movies = get_random_movies()

    for canvas, title_label in zip(canvases, title_labels):
        #display movie poster on the canvas
        if random_movies:
            movie = random_movies.pop(0)  #pop the first movie from the list
            poster_url = f"https://image.tmdb.org/t/p/w500/{movie.get('poster_path', '')}"
            response = requests.get(poster_url)
            img_data = Image.open(BytesIO(response.content))
            img_data.thumbnail((140, 190))

            img = ImageTk.PhotoImage(img_data)
            canvas.create_image(0, 0, anchor=tk.NW, image=img)
            canvas.image = img

            #update label for movie title
            title_label.config(text=truncate_title(movie.get("title", "")))


def get_random_movies():
    #gets a set of random movies to avoid duplicates
    url = "https://api.themoviedb.org/3/movie/popular"
    params = {"api_key": TMDB_API_KEY}
    response = requests.get(url, params=params)
    data = response.json()
    movies = data.get("results", [])

    #shuffles the list of movies to get a random order
    random.shuffle(movies)

    return movies

def truncate_title(title, max_length=13):
    #truncate or use ellipses for long titles
    return title[:max_length] + "..." if len(title) > max_length else title


def get_movie_info(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": movie_name}

    response = requests.get(url, params=params)
    data = response.json()

    #get movie information
    movie_info = data.get("results", [])

    if movie_info:
        #get movie details
        movie_id = movie_info[0]["id"]
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        params = {"api_key": TMDB_API_KEY}

        response = requests.get(url, params=params)
        details = response.json()

        #get movie images
        movie_images = get_movie_images(movie_id)

        #get genres and rating
        genres = ", ".join(genre["name"] for genre in details.get("genres", []))
        rating = details.get("vote_average", "N/A")

        return movie_info, movie_images, genres, rating

    return [], [], "N/A", "N/A"


def get_movie_images(movie_id):
    if movie_id:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/images"
        params = {
            "api_key": TMDB_API_KEY,
        }

        response = requests.get(url, params=params)
        data = response.json()

        #gets the poster path for each image
        poster_paths = [image["file_path"] for image in data.get("posters", [])]

        #construct the full URL for each poster image
        base_url = "https://image.tmdb.org/t/p/original"
        poster_urls = [f"{base_url}{path}" for path in poster_paths]

        return poster_urls

    return []


def search_page():
    global canvas, output_text, next_button, prev_button

    def perform_search(movie_name, canvas, output_text, button_frame):
        #fetch movie information from TMDb API
        global movie_info, movie_images, genres, rating
        movie_info, movie_images, genres, rating = get_movie_info(movie_name)

        #displays movie information and images
        display_movie_info(
            movie_info, output_text, genres, rating, 0
        )  #display the first movie's info
        display_movie_images(
            movie_info, movie_images, canvas, button_frame, 0
        )  #display the first movie's image

    def display_movie_info(movie_info, output_text, genres, rating, index):
        #clear the existing content
        output_text.delete(1.0, tk.END)

        if movie_info:
            #display information for the current movie
            movie = movie_info[index]
            title = movie.get("title", "N/A")
            overview = movie.get("overview", "N/A")
            release_date = movie.get("release_date", "N/A")

            #modify font and size
            text_format = f"{title}\n\nOverview:\n{overview}\n\nRelease Date: {release_date}\nGenres: {''.join(genres)}\nRating: {rating}\n\n"
            output_text.insert(tk.END, text_format)
            
            #apply bold to the title
            output_text.tag_add("bold_title", "1.0", "2.0")
            output_text.tag_configure("bold_title", font=("Montserrat", 20, "bold"), foreground="white")

            #apply bold to "Overview:"
            output_text.tag_add("bold_overview", "3.0", "3.9")  # Adjust the indices based on your text
            output_text.tag_configure("bold_overview", font=("Montserrat", 13, "bold"), foreground="white")
            
            #apply normal font to the entire text
            output_text.tag_add("normal", "4.0", "4.end")
            output_text.tag_configure("normal", font=("Montserrat", 11, "normal"), foreground="white")
            
            #apply bold to "Release Date:"
            output_text.tag_add("bold_release_date", "6.0", "6.12")  # Adjust the indices based on your text
            output_text.tag_configure("bold_release_date", font=("Montserrat", 13, "bold"), foreground="white")
            
            #find the index of "Release Date:" in the text
            release_date_index = text_format.find("Release Date:")

            #apply normal font to the text after "Release Date:"
            output_text.tag_add("normal", f"5.{release_date_index + 11}", tk.END)
            output_text.tag_configure("normal", font=("Montserrat", 11, "normal"), foreground="white")
            
            #apply bold to the genres
            output_text.tag_add("bold_genres", "7.0", "7.7")
            output_text.tag_configure("bold_genres", font=("Montserrat", 13, "bold"), foreground="white")
            
            #apply bold to the rating
            output_text.tag_add("bold_rating", "8.0", "8.7")
            output_text.tag_configure("bold_rating", font=("Montserrat", 13, "bold"), foreground="white")
            
        else:
            output_text.insert(tk.END, "No movies found.")
            
    def display_movie_images(movie_info, movie_images, canvas, button_frame, index):
        #clear the existing content
        canvas.delete("all")

        #destroy existing buttons to avoid duplication
        for widget in button_frame.winfo_children():
            widget.destroy()

        #display movie images on the canvas
        total_images = len(movie_images)

        if total_images == 0:
            canvas.create_text(
                100,
                150,
                text="No images available",
                fill="white",
                font=("Montserrat", 14),
            )
            return

        def show_image(index):
            nonlocal current_movie_index
            current_movie_index = index

            #fetch and display the selected image
            response = requests.get(movie_images[current_movie_index])
            img_data = Image.open(BytesIO(response.content))
            img_data.thumbnail((500, 300))

            img = ImageTk.PhotoImage(img_data)
            canvas.create_image(0, 0, anchor=tk.NW, image=img)
            canvas.image = img  #keep a reference to the image to prevent it from being garbage collected

            #display information for the current movie
            display_movie_info(
                movie_info, output_text, genres, rating, current_movie_index
            )

        def next_movie():
            nonlocal current_movie_index
            current_movie_index = (current_movie_index + 1) % total_images
            show_image(current_movie_index)

        def prev_movie():
            nonlocal current_movie_index
            current_movie_index = (current_movie_index - 1) % total_images
            show_image(current_movie_index)

        #initial display
        show_image(index)

        #create "Next" button
        next_button = tk.Button(
            button_frame,
            text="Next",
            command=next_movie,
            font=("Montserrat", 10, "bold"),
            bg="#363636",
            fg="#c3c3c3",
        )
        next_button.pack(side=tk.RIGHT, padx=10)

        #create "Previous" button
        prev_button = tk.Button(
            button_frame,
            text="Previous",
            command=prev_movie,
            font=("Montserrat", 10, "bold"),
            bg="#363636",
            fg="#c3c3c3",
        )
        prev_button.pack(side=tk.LEFT, padx=10)

    search_frame = tk.Frame(main_frame, bg="#232323")

    #text "Search Movies:"
    search_label = tk.Label(
        search_frame,
        text="Search Movies:",
        font=("Montserrat", 25, "bold"),
        fg="white",
        bg="#232323",
    )
    search_label.grid(
        row=0, column=0, padx=10, pady=(5, 50), sticky="w"
    )

    entry = tk.Entry(search_frame, width=32, font=("Montserrat", 15), fg="#232323")
    entry.grid(
        row=0, column=0, padx=15, pady=(100, 10)
    )

    search_button = tk.Button(
        search_frame,
        text="Search",
        font=("Montserrat", 10, "bold"),
        bg="#363636",
        fg="#c3c3c3",
        command=lambda: perform_search(entry.get(), canvas, output_text, button_frame),
    )
    search_button.grid(
        row=0, column=1, padx=10, pady=(100, 10), sticky="ew"
    )  #adjusted pady values to be the same as the entry

    #text widget for displaying search results
    output_text = tk.Text(search_frame, wrap="word", width=52, height=18.5, relief="flat")
    output_text.grid(row=1, column=0, columnspan=1, padx=1, pady=40)
    output_text.configure(bg="#232323")

    #canvas widget for displaying movie images
    canvas = tk.Canvas(search_frame, width=198, height=300, bg="#232323")
    canvas.grid(row=1, column=1, pady=10, padx=1)

    #frame to hold Next and Previous buttons
    button_frame = tk.Frame(search_frame, bg="#232323")
    button_frame.grid(row=2, column=0, columnspan=4, pady=10)

    #variable to keep track of the current movie index
    current_movie_index = 0

    search_frame.pack(padx=20)


def about_page():
    about_frame = tk.Frame(main_frame, bg="#232323")  #set background color

    #load the about image
    about_image = Image.open("Images\welcome.png")
    about_photo = ImageTk.PhotoImage(about_image)

    #create a label for the about image
    about_image_label = tk.Label(about_frame, image=about_photo, bg="#232323")
    about_image_label.image = about_photo
    about_image_label.pack(pady=175)

    about_frame.pack(padx=15)


def indicate(page):
    delete_page()
    page()


def delete_page():
    for widget in main_frame.winfo_children():
        widget.destroy()


root = tk.Tk()
root.geometry("744x670")
root.title("MovieLizd by ADAM JOHN SIMBULAN")

options_frame = tk.Frame(root, bg="#363636")

#load the logo image
logo_image = Image.open("Images\logom.png")
logo_photo = ImageTk.PhotoImage(logo_image)

#create a button using Label for the logo
logo_button = tk.Label(options_frame, image=logo_photo, bg="#363636", cursor="hand2")
logo_button.image = logo_photo
logo_button.place(x=30, y=23)

#bind the logo label to the about_page function
logo_button.bind("<Button-1>", lambda event: indicate(about_page))

home_btn = tk.Button(
    options_frame,
    text="Home",
    font=("Montserrat", 14, "bold"),
    fg="#c3c3c3",
    bd=0,
    bg="#363636",
    command=lambda: indicate(home_page),
)
home_btn.place(x=535, y=13)

search_btn = tk.Button(
    options_frame,
    text="Search",
    font=("Montserrat", 14, "bold"),
    fg="#c3c3c3",
    bd=0,
    bg="#363636",
    command=lambda: indicate(search_page),
)
search_btn.place(x=620, y=13)

options_frame.pack(side=tk.TOP)
options_frame.pack_propagate(False)
options_frame.configure(width=744, height=70)

main_frame = tk.Frame(
    root, highlightbackground="#232323", highlightthickness=2, bg="#232323"
)
main_frame.pack(side=tk.TOP)
main_frame.pack_propagate(False)
main_frame.configure(height=670, width=744, bg="#232323")

#show the about page when the code is run
indicate(about_page)

root.resizable(width=False, height=False)
root.mainloop()
