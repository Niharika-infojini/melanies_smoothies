
# Import Python packages
import streamlit as st
import requests

from snowflake.snowpark.functions import col

# Page title
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write("Choose the fruits you want in your custom Smoothie!")

# Get customer name
name_on_order = st.text_input("Name on Smoothie:")

st.write("The name on your Smoothie will be:", name_on_order)

# Connect to Snowflake
try:
    cnx = st.connection("snowflake")
    session = cnx.session()

    # Retrieve fruit details from Snowflake
    my_dataframe = session.table(
        "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
    ).select(
        col("FRUIT_NAME"),
        col("SEARCH_ON")
    )

    # Fetch Snowflake data
    fruit_rows = my_dataframe.collect()

    # Create fruit list for Streamlit
    fruit_options = [
        row["FRUIT_NAME"] for row in fruit_rows
    ]

    # Create a dictionary to map fruit names to search values
    fruit_search = {
        row["FRUIT_NAME"]: row["SEARCH_ON"]
        for row in fruit_rows
    }

    st.success("Connected to Snowflake successfully!")

except Exception as e:
    st.error("Unable to retrieve fruit data from Snowflake.")
    st.exception(e)
    st.stop()


# Display fruit selection
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients",
    fruit_options,
    max_selections=5
)


# Process selected ingredients
if ingredients_list:

    ingredients_string = " ".join(ingredients_list)

    for fruit_chosen in ingredients_list:

        search_on = fruit_search[fruit_chosen]

        st.subheader(fruit_chosen + " Nutrition Information")

        try:
            smoothiefroot_response = requests.get(
                f"https://my.smoothiefroot.com/api/fruit/{search_on}",
                timeout=15
            )

            smoothiefroot_response.raise_for_status()

            # Display nutrition information
            st.json(smoothiefroot_response.json())

        except requests.RequestException as e:
            st.error(f"Unable to fetch information for {fruit_chosen}: {e}")

        except ValueError:
            st.error(f"Invalid nutrition data received for {fruit_chosen}.")


    # Submit smoothie order
    if st.button("Submit Order"):

        if not name_on_order.strip():
            st.warning("Please enter your name before submitting.")

        else:
            try:
                # Insert order into Snowflake safely
                insert_query = """
                    INSERT INTO SMOOTHIES.PUBLIC.ORDERS
                    (INGREDIENTS, NAME_ON_ORDER)
                    VALUES (?, ?)
                """

                session.sql(
                    insert_query,
                    params=[
                        ingredients_string,
                        name_on_order.strip()
                    ]
                ).collect()

                st.success(
                    "Your Smoothie is ordered!",
                    icon="✅"
                )

            except Exception as e:
                st.error("Unable to submit your smoothie order.")
                st.exception(e)
