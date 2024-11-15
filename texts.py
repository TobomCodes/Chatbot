import requests
from bs4 import BeautifulSoup
import os

# Define the base URL
base_url = "https://battle-cats.fandom.com/wiki/Heavenly_Tower/Floor_"

# Directory to store each floor's content
output_dir = "heavenly_tower_floors"
os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

for i in range(1, 51):  # Loop through Floor 1 to Floor 50
    # Construct the URL for each floor
    url = f"{base_url}{i}"

    # Fetch the page content
    response = requests.get(url)

    # Check if the response is successful
    if response.status_code != 200:
        print(f"Failed to fetch Floor {i}. Status code: {response.status_code}")
        continue

    print(f"Successfully fetched Floor {i}")

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract text content
    page_text = soup.get_text(separator="\n", strip=True)

    # Split content at "Reference" and keep only the part before it
    if "Reference" in page_text:
        page_text = page_text.split("comments")[0]  # Get content before "Reference"
        print(f"'comments' found on Floor {i}. Content truncated.")

    # Define the file path for the current floor
    floor_file_path = os.path.join(output_dir, f"Floor_{i}.txt")

    # Write the data to the file for each floor
    with open(floor_file_path, "w", encoding="utf-8") as file:
        file.write(page_text)

    print(f"Data for Floor {i} written to {floor_file_path}")
