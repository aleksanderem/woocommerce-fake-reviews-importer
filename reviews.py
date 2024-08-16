import random
import time
import json
import argparse
from datetime import datetime, timedelta
from woocommerce import API

# ANSI color codes
RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
WHITE = "\033[97m"
DIM = "\033[2m"
ITALIC = "\033[3m"

# WooCommerce API Configuration
wcapi = API(
    url="http://localhost:10033",
    consumer_key="ck_dd5f764b1f1343683634fe3756641a62a4c3134b",
    consumer_secret="cs_9346cbd8f4ad315f7c82a49ffd1a7c51aafcb387",
    version="wc/v3",
    timeout=120  # Set a global timeout of 120 seconds
)

# Function to load data from a JSON file
def load_json(file):
    try:
        with open(file, 'r') as f:
            data = json.load(f)
            return data if data else []
    except json.JSONDecodeError:
        return []

# Function to generate a random date
def generate_random_date(start_date, end_date):
    return start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds())),
    )

# Function to select a rating based on percentage distribution
def select_rating(percentage_distribution):
    ratings = []
    for rating, percentage in percentage_distribution.items():
        ratings.extend([rating] * int(percentage * 100))
    selected_rating = random.choice(ratings)
    print(f"{WHITE}Selected rating: {selected_rating} stars{RESET}")
    return selected_rating

# Function to import reviews
def import_reviews(rating_files, names, start_date, end_date, max_reviews_per_product, product_ids, percentage_distribution, replies, delay_min, delay_max, reviewer, reviewer_email):
    product_review_count = {product_id: 0 for product_id in product_ids}
    used_names_per_product = {product_id: set() for product_id in product_ids}

    for product_id in product_ids:
        # Randomize the number of reviews for this product
        reviews_to_add = random.randint(1, max_reviews_per_product)
        print(f"{WHITE}Will add {reviews_to_add} reviews to product ID {product_id}{RESET}")

        while product_review_count[product_id] < reviews_to_add:
            rating = select_rating(percentage_distribution)
            file = rating_files[rating]
            reviews = load_json(file)

            review = random.choice(reviews) if reviews else {"review": ""}  # Handle empty files

            # Select a random name and ensure it hasn't been used for this product
            name = random.choice(names["names"])
            while name in used_names_per_product[product_id]:
                name = random.choice(names["names"])

            # Track the name used for this product
            used_names_per_product[product_id].add(name)
            print(f"{WHITE}Selected reviewer name: {name} for product ID {product_id}{RESET}")

            review_date = generate_random_date(start_date, end_date)
            print(f"{WHITE}Adding review for product ID {product_id}...{RESET}")
            print(f"{WHITE}Review date: {review_date}{RESET}")

            # Display the review content with formatting
            print(f"{DIM}{ITALIC}Review content: {review['review']}{RESET}")

            # Add the review to WooCommerce
            review_data = {
                "product_id": product_id,
                "review": review["review"],  # May be empty
                "reviewer": name,
                "reviewer_email": f"{name.lower()}@example.com",
                "rating": rating,
                "date_created": review_date.isoformat(),
                "status": "approved",
                "verified": True  # Mark the review as from a verified customer
            }

            response = wcapi.post("products/reviews", review_data)

            if response.status_code == 201:
                product_review_count[product_id] += 1
                review_id = response.json()["id"]
                print(f"{GREEN}Review for product {product_id} added. Total reviews for this product: {product_review_count[product_id]}.{RESET}")

                # Reply to the review
                reply_to_review(review_id, rating, review_date, replies, reviewer, reviewer_email, product_id)

                # Delay before adding the next review
                delay = random.randint(delay_min, delay_max)
                print(f"{WHITE}Waiting {delay} seconds before adding the next review...{RESET}")
                time.sleep(delay)
            else:
                print(f"{RED}Failed to add review for product {product_id}. Error: {response.status_code}{RESET}")

# Function to reply to reviews using the custom endpoint
def reply_to_review(review_id, expected_rating, review_date, replies, reviewer, reviewer_email, product_id):
    # Fetch the review details to verify
    response = wcapi.get(f"products/reviews/{review_id}")

    if response.status_code == 200:
        review_data = response.json()

        # Verify the product ID and rating
        if review_data.get('product_id') == product_id and review_data.get('rating') == expected_rating:
            # Check if there are replies available for this rating
            if str(expected_rating) in replies["replies"]:
                available_replies = replies["replies"][str(expected_rating)]

                # Check if there are existing replies to avoid duplicates
                existing_replies = wcapi.get(f"products/reviews/{review_id}/replies")
                if existing_replies.status_code == 200:
                    existing_reply_texts = [reply_text['review'] for reply_text in existing_replies.json()]
                    available_replies = [reply for reply in available_replies if reply not in existing_reply_texts]

                # Only proceed if there are available replies that haven't been used yet
                if available_replies:
                    reply = random.choice(available_replies)
                    reply_date = review_date + timedelta(minutes=random.randint(60, 360))  # 60 minutes to 6 hours

                    print(f"{WHITE}Replying to review ID {review_id} with rating {expected_rating} stars. Reply date: {reply_date}{RESET}")

                    # Display the reply content with formatting
                    print(f"{DIM}{ITALIC}Reply content: {reply}{RESET}")

                    reply_data = {
                        "id": review_id,
                        "reviewer": reviewer,  # Replace with the desired username
                        "reviewer_email": reviewer_email,  # Add a valid email address
                        "review": reply,
                        "date_created": reply_date.isoformat(),
                    }

                    # Make a POST request to the custom endpoint
                    response = wcapi.post(f"reviews/{review_id}/reply", reply_data)

                    # Treat both 200 and 201 as successful responses
                    if response.status_code == 200 or response.status_code == 201:
                        print(f"{GREEN}Reply to review {review_id} added successfully. Response: {response.json()}{RESET}")
                    else:
                        print(f"{RED}Failed to add reply to review {review_id}. Error: {response.status_code}, Response: {response.json()}{RESET}")
                else:
                    print(f"{WHITE}No available replies for rating {expected_rating}, or all replies have already been used. Skipping...{RESET}")
            else:
                print(f"{RED}No replies found for rating {expected_rating}. Skipping...{RESET}")
        else:
            print(f"{RED}Review ID {review_id} does not match expected product ID {product_id} or rating {expected_rating}. Skipping reply.{RESET}")
    else:
        print(f"{RED}Failed to fetch review details for review ID {review_id}. Error: {response.status_code}, Response: {response.json()}{RESET}")

# Main function to handle command-line arguments
def main():
    parser = argparse.ArgumentParser(description="Import reviews to WooCommerce products.")
    parser.add_argument("--product_ids", nargs='+', type=int, help="Specify a list of product IDs to add reviews to.")
    parser.add_argument("--delay_min", type=int, default=4, help="Minimum delay in seconds between adding reviews.")
    parser.add_argument("--delay_max", type=int, default=10, help="Maximum delay in seconds between adding reviews.")
    parser.add_argument("--rating_files", nargs=5, type=str, default=["ratings_1.json", "ratings_2.json", "ratings_3.json", "ratings_4.json", "ratings_5.json"], help="Specify the JSON files for each rating (1-5 stars).")
    parser.add_argument("--names_file", type=str, default="names.json", help="Specify the JSON file containing reviewer names.")
    parser.add_argument("--replies_file", type=str, default="replies.json", help="Specify the JSON file containing reply templates.")
    parser.add_argument("--start_date", type=str, default="2023-08-01", help="Specify the start date for the reviews (YYYY-MM-DD).")
    parser.add_argument("--end_date", type=str, default="2023-08-15", help="Specify the end date for the reviews (YYYY-MM-DD).")
    parser.add_argument("--max_reviews_per_product", type=int, default=5, help="Specify the maximum number of reviews per product.")
    parser.add_argument("--percentage_distribution", nargs=5, type=float, default=[0.02, 0.00, 0.10, 0.40, 0.48], help="Specify the percentage distribution for ratings 1-5 stars (e.g., 0.02 0.00 0.10 0.40 0.48).")
    parser.add_argument("--reviewer", type=str, default="Jarek z Pięknesny.pl", help="Specify the name of the reviewer replying to reviews.")
    parser.add_argument("--reviewer_email", type=str, default="jaroslaw.skrzypczuk@gmail.com", help="Specify the email of the reviewer replying to reviews.")
    args = parser.parse_args()

    # Load JSON data from files
    rating_files = {i+1: args.rating_files[i] for i in range(5)}
    names = load_json(args.names_file)
    replies = load_json(args.replies_file)

    # Parse the start and end dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    # List of product IDs to which reviews should be added
    product_ids = args.product_ids if args.product_ids else [100933, 100922]  # Default product IDs

    # Percentage distribution of ratings
    percentage_distribution = {i+1: args.percentage_distribution[i] for i in range(5)}

    print(f"{WHITE}Starting the import of reviews...{RESET}")
    import_reviews(rating_files, names, start_date, end_date, args.max_reviews_per_product, product_ids, percentage_distribution, replies, args.delay_min, args.delay_max, args.reviewer, args.reviewer_email)
    print(f"{WHITE}Finished importing reviews.{RESET}")

if __name__ == "__main__":
    main()
