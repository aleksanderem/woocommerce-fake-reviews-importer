# WooCommerce Review Importer and Reply System Documentation

### Author: Alex Miesak 
## Overview

This documentation outlines the usage of a custom Python script designed to automate the process of importing reviews into WooCommerce products and replying to those reviews using a custom REST API endpoint. The system consists of two main components:

1. **WooCommerce Review Importer Script**: A Python script that generates and imports reviews into WooCommerce, and optionally replies to those reviews.
2. **Helper Plugin for Automated Reviews**: A WordPress plugin that provides a custom REST API endpoint to handle replies to WooCommerce reviews.

## Prerequisites

- **WooCommerce Store**: A running WooCommerce store with API keys generated.
- **WordPress Plugin Installation**: The custom plugin must be installed and activated on your WooCommerce site.
- **Python 3.x**: Installed on your system.
- **Required Python Packages**: Install the necessary packages using pip:
  ```bash
  pip install requests woocommerce argparse
  ```

## WooCommerce API Configuration

Before using the Python script, you need to configure it with your WooCommerce API credentials. Open the script and modify the following section with your store's details:

```python
wcapi = API(
    url="http://your-woocommerce-site.com",  # Replace with your WooCommerce store URL
    consumer_key="your_consumer_key",        # Replace with your WooCommerce API consumer key
    consumer_secret="your_consumer_secret",  # Replace with your WooCommerce API consumer secret
    version="wc/v3",
    timeout=120  # Set a global timeout of 120 seconds
)
```

### Obtaining WooCommerce API Keys

1. **Log in to your WooCommerce site.**
2. **Navigate to `WooCommerce` > `Settings` > `Advanced` > `REST API`.**
3. **Click `Add Key` and generate the API keys.**
4. **Copy the `Consumer Key` and `Consumer Secret`.**

## Helper Plugin for Automated Reviews

### Plugin Overview

This custom WordPress plugin adds a REST API endpoint that allows external systems (like the Python script) to reply to WooCommerce reviews. The plugin is essential for the proper functioning of the review reply feature in the Python script.

### Plugin Code

```php
<?php
/*
Plugin Name: Helper plugin for automated reviews generator
Description: Adds a custom REST API endpoint to reply to WooCommerce reviews.
Version: 1.0
Author: Alex M.
*/

if ( ! defined( 'ABSPATH' ) ) {
  exit; // Exit if accessed directly.
}

class WC_Custom_Review_Reply_Endpoint {
  public function __construct() {
    add_action( 'rest_api_init', array( $this, 'register_routes' ) );
  }
  
  public function register_routes() {
    register_rest_route( 'wc/v3', '/reviews/(?P<id>\d+)/reply', array(
        'methods'  => 'POST',
        'callback' => array( $this, 'handle_review_reply' ),
        'permission_callback' => function () {
          return current_user_can( 'manage_woocommerce' );
        },
    ));
  }
  
  public function handle_review_reply( $request ) {
    $review_id = $request['id'];
    $reply_data = $request->get_json_params();
    $date_created = sanitize_text_field($reply_data['date_created']);
    
    // Validate the review ID
    if ( ! $review_id || ! get_comment( $review_id ) ) {
      return new WP_Error( 'invalid_review', 'Invalid review ID.', array( 'status' => 404 ) );
    }
    
    $review = get_comment($review_id);
    if (!$review) {
      return new WP_Error('rest_comment_invalid_id', __('Invalid review ID.'), array('status' => 404));
    }

    // Validate required fields
    if ( empty( $reply_data['reviewer'] ) || empty( $reply_data['review'] ) ) {
      return new WP_Error( 'missing_fields', 'Reviewer name and review content are required.', array( 'status' => 400 ) );
    }
    
    // Add the reply as a comment to the review
    $reply_id = wp_insert_comment( array(
        'comment_post_ID' => $review->comment_post_ID,
        'comment_parent'  => $review_id,
        'comment_type' => '',
        'comment_author'  => sanitize_text_field( $reply_data['reviewer'] ),
        'comment_author_email' => sanitize_email( $reply_data['reviewer_email'] ),
        'comment_content' => sanitize_textarea_field( $reply_data['review'] ),
        'comment_date'    => $date_created,
        'comment_approved' => 1,
    ));
    
    if ( ! $reply_id ) {
      return new WP_Error( 'cannot_reply', 'Failed to add reply to the review.', array( 'status' => 500 ) );
    }
    
    return array(
        'success' => true,
        'reply_id' => $reply_id,
    );
  }
}

new WC_Custom_Review_Reply_Endpoint();
```

### Plugin Installation

1. **Create a new directory in your WordPress installation’s `wp-content/plugins/` folder, e.g., `wc-review-reply-endpoint`.**
2. **Create a PHP file inside this directory, e.g., `wc-review-reply-endpoint.php`.**
3. **Copy the plugin code provided above into the file.**
4. **Activate the plugin** from the WordPress admin dashboard under `Plugins`.

## WooCommerce Review Importer Script

### Script Overview

This Python script automates the process of importing reviews into WooCommerce products. The reviews can be generated based on JSON files containing review content, reviewer names, and reply templates. The script also allows for the automatic posting of replies to the reviews using the custom REST API endpoint provided by the WordPress plugin.

### Script Features

- **Import reviews based on customizable JSON files.**
- **Specify custom delay intervals between adding reviews.**
- **Control the rating distribution across reviews.**
- **Randomize the number of reviews per product.**
- **Automatically reply to reviews using a custom REST API endpoint.**
- **Specify reviewer details and review content.**

### Command-Line Arguments

- **`--product_ids`**: Specify one or more product IDs to add reviews to.
    - Example: `--product_ids 100933 100922`

- **`--delay_min`**: Set the minimum delay in seconds between adding reviews.
    - Default: `4`
    - Example: `--delay_min 10`

- **`--delay_max`**: Set the maximum delay in seconds between adding reviews.
    - Default: `10`
    - Example: `--delay_max 20`

- **`--rating_files`**: Specify the JSON files for each rating (1-5 stars).
    - Default: `["ratings_1.json", "ratings_2.json", "ratings_3.json", "ratings_4.json", "ratings_5.json"]`
    - Example: `--rating_files ratings1.json ratings2.json ratings3.json ratings4.json ratings5.json`

- **`--names_file`**: Specify the JSON file containing reviewer names.
    - Default: `"names.json"`
    - Example: `--names_file custom_names.json`

- **`--replies_file`**: Specify the JSON file containing reply templates.
    - Default: `"replies.json"`
    - Example: `--replies_file custom_replies.json`

- **`--start_date`**: Specify the start date for the reviews (YYYY-MM-DD).
    - Default: `"2023-08-01"`
    - Example: `--start_date 2023-09-01`

- **`--end_date`**: Specify the end date for the reviews (YYYY-MM-DD).
    - Default: `"2023-08-15"`
    - Example: `--end_date 2023-09-30`

- **`--max_reviews_per_product`**: Specify the maximum number of reviews per product. The script will randomly determine the number of reviews between 1 and this maximum value.
    - Default: `5`
    - Example: `--max_reviews_per_product 10`

- **`--percentage_distribution`**: Specify the percentage distribution for ratings 1-5 stars.
    - Default: `0.02 0.00 0.10 0.40 0.48`
    - Example: `--percentage_distribution 0.05 0.05 0.20 0.30 0.40`

- **`--reviewer`**: Specify the name of the reviewer replying to reviews.
    - Default: `"Display name of admin"`
    - Example: `--reviewer "Admin"`

- **`--reviewer_email`**: Specify the email of the reviewer replying to reviews.
    - Default: `"mail@example.com"`
    - Example: `--reviewer_email "admin@example.com"`

### Example Commands

1. **Run the script with default settings**:
   ```bash
   python script_name.py
   ```

2. **Run the script for specific product IDs with custom delay intervals**:
   ```bash
   python script_name.py --product_ids 100933 100922 --delay_min 10 --delay_max 20
   ```

3. **Run the script with a custom rating distribution and reviewer info**:
   ```bash
   python script_name.py --percentage_distribution 0.05 0.05 0.20 0.30 0.40 --reviewer "Admin" --reviewer_email "admin@example.com"
   ```

### Script Workflow

1. **Load JSON Data**: The script loads rating files, names, and replies from the specified JSON files.
2. **Select Product IDs**: Product IDs can be passed as arguments or retrieved via WP-CLI.
3. **Generate Reviews**: Reviews are generated with random content from the JSON files and assigned to the specified products.
4. **Randomize Review Count**: For each product, a random number of reviews (between 1 and the maximum specified) is chosen.
5. **Apply Delay**: The script waits for a random amount of time between adding reviews based on the specified delay range.
6. **Add Replies**: If configured, replies are automatically added to the reviews using the custom endpoint.

## Troubleshooting

- **Invalid Product IDs**: Ensure the product IDs provided exist in your WooCommerce store.
- **API Connection Issues**: Verify that the WooCommerce API keys are correct and that the WooCommerce store URL is accessible.
- **Custom Endpoint Issues**: Ensure the custom WooCommerce plugin is installed and activated correctly.
- **Review & Reply Mismatch**: The script includes checks to ensure replies are added to the correct reviews. If issues arise, verify the plugin and script logic.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---
