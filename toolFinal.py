import requests
from bs4 import BeautifulSoup
import json
import tkinter as tk
from tkinter import ttk
from urllib.parse import urljoin
import urllib.request

def get_file_size(url):
    response = requests.get(url)
    if response.status_code == 200:
        return int(response.headers.get('content-length', 0))
    else:
        return 0

def generate_report():
    # Get the website URL from the text input
    url = url_input.get()
    session = requests.Session()
    # get the HTML content
    html = session.get(url).content
    # Make a request to the website and parse the HTML
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract relevant metrics from the HTML using BeautifulSoup
    page_title = soup.title.string
    num_links = len(soup.find_all('a'))
    num_images = len(soup.find_all('img'))
    page_size = response.headers.get('content-length', 0)
    load_time = response.elapsed.total_seconds()
    html_size = len(response.content)
    total_redirects = len(response.history)
    num_headings = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
    num_pages = len(soup.find_all('a'))
    num_videos = len(soup.find_all('video'))
    num_forms = len(soup.find_all('form'))

    script_files = []
    css_files = []
    image_files = []

    # Fetch script files
    for script in soup.find_all("script"):
        if script.attrs.get("src"):
            script_url = urljoin(url, script.attrs.get("src"))
            script_files.append(script_url)

    # Fetch CSS files
    for css in soup.find_all("link"):
        if css.attrs.get("href") and css.attrs.get("rel") == "stylesheet":
            css_url = urljoin(url, css.attrs.get("href"))
            css_files.append(css_url)

    # Fetch image files
    for image in soup.find_all("img"):
        if image.attrs.get("src"):
            image_url = urljoin(url, image.attrs.get("src"))
            image_files.append(image_url)

    # Fetch file sizes
    script_sizes = [get_file_size(script_url) for script_url in script_files]
    #print(sum(script_sizes))
    css_sizes = [get_file_size(css_url) for css_url in css_files]
    #print(sum(css_sizes))
    image_sizes = [get_file_size(image_url) for image_url in image_files]
    #print(sum(image_sizes))

    api_url = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=' + \
        url + '&strategy=mobile'
    headers = {'Accept-Encoding': 'gzip'}
    response = requests.get(api_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = json.loads(response.text)

    if 'lighthouseResult' in data:
        # FCP (First Contentful Paint)
        fcp = data['lighthouseResult']['audits']['first-contentful-paint']['numericValue'] /1000
        # LCP (Largest Contentful Paint)
        lcp = data['lighthouseResult']['audits']['largest-contentful-paint']['numericValue'] / 1000
        # Speed Index
        speed_index = data['lighthouseResult']['audits']['speed-index']['numericValue'] /1000
        # DOM Size
        dom_size = data['lighthouseResult']['audits']['dom-size']['numericValue']
        # QLS (Total Blocking Time)
        qls = data['lighthouseResult']['audits']['cumulative-layout-shift']['numericValue']
        # Overall Performance Score
        overall_score = data["lighthouseResult"]["categories"]["performance"]["score"] * 100
    elif 'loadingExperience' in data:
        # FCP (First Contentful Paint)
        fcp = data['loadingExperience']['metrics']['FIRST_CONTENTFUL_PAINT_MS']['percentile']
        # LCP (Largest Contentful Paint)
        lcp = data['loadingExperience']['metrics']['LARGEST_CONTENTFUL_PAINT_MS']['percentile']
        # Speed Index
        speed_index = data['loadingExperience']['metrics']['SPEED_INDEX_MS']['percentile']
        # DOM Size
        dom_size = data['loadingExperience']['metrics']['DOM_SIZE']['percentile']
        # QLS (Total Blocking Time)
        qls = data['loadingExperience']['metrics']['CUMULATIVE_LAYOUT_SHIFT_SCORE']['percentile']
        # Overall Performance Score
        overall_score = data["loadingExperience"]["categories"]["performance"]["score"] * 100
    else:
        print("Unable to retrieve data.")
        return
    # Update the report label with the metrics
    report_label.config(
        text=f'Website metrics for \nPage Title: {page_title}\nURL: {url}\n\n\nOverall Performance Score: {overall_score}\n', fg='black', font=3)
    # Create a table to display the metrics
    table = ttk.Treeview(window, columns=("Metric", "Value", "Unit"), show="headings")
    table.heading("Metric", text="Metric")
    table.heading("Value", text="Value")
    table.heading("Unit", text="Unit")
    table.column("Metric", width=200) 
    table.column("Value", width=100)
    table.column("Unit", width=100)
    table.insert("", tk.END, values=("First Contentful Paint", fcp, "seconds"))
    table.insert("", tk.END, values=("Largest Contentful Paint", lcp, "seconds"))
    table.insert("", tk.END, values=("Speed Index", speed_index, "seconds"))
    table.insert("", tk.END, values=("DOM Size", dom_size, "elements"))
    table.insert("", tk.END, values=("Cumulative Layout Shift", qls, "seconds"))
    table.insert("", tk.END, values=("Load Time", load_time, "seconds"))
    table.insert("", tk.END, values=("HTML Size", html_size / 1024 , "KiloBytes (kb)"))
    table.insert("", tk.END, values=("Image Size", sum(image_sizes) / 1024 , "KiloBytes (kb)"))
    table.insert("", tk.END, values=("Script Size", sum(script_sizes) / 1024 , "KiloBytes (kb)"))
    table.insert("", tk.END, values=("CSS Size", sum(css_sizes) / 1024 , "KiloBytes (kb)"))
    table.insert("", tk.END, values=("Total Size (HTML+CSS+Script+Image)", (html_size+sum(css_sizes)+sum(script_sizes)+sum(image_sizes))/1024, "KiloBytes (kb)"))
    table.insert("", tk.END, values=("Total Redirects", total_redirects, "times"))
    table.insert("", tk.END, values=("Number of Links", num_links, "#"))
    table.insert("", tk.END, values=("Number of Forms", num_forms, "#"))
    table.insert("", tk.END, values=("Number of Images", num_images, "#"))
    table.insert("", tk.END, values=("Number of Headings", num_headings, "#"))
    table.insert("", tk.END, values=("Number of Pages", num_pages, "#"))
    table.insert("", tk.END, values=("Number of Videos", num_videos, "#"))


    table.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Adjust window size based on the number of rows in the table
    table_height = len(table.get_children()) * 25
    window.geometry(f"600x{table_height+220}")


# Create the GUI window
window = tk.Tk()
window.title('Web Analysis Tool')

# Create the URL input label and text input
url_label = tk.Label(window, text='Enter website URL:', width=70, height=4)
url_input = tk.Entry(window, width=30)

# Create the generate report button
button1 = tk.Button(window, text='Generate Report', fg='white',
                    width=35, bg='grey', command=generate_report)

# Create the report label
report_label = tk.Label(window, text='')

# Pack the elements into the window
url_label.pack()
url_input.pack()
button1.pack(pady=10)
report_label.pack()


# Run the main loop
window.mainloop()