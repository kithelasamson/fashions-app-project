import json
import webbrowser
import requests

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

PHONE_NUMBER = "254757486132"

API_URL = "http://YOUR_SERVER_URL:5000"


class ShopApp(App):

    def build(self):

        with open("products.json", "r") as f:
            self.data = json.load(f)

        self.cart = []

        self.root_layout = BoxLayout(
            orientation="vertical"
        )

        self.show_categories()

        return self.root_layout

    # --------------------
    # Categories
    # --------------------

    def show_categories(self):

        self.root_layout.clear_widgets()

        self.root_layout.add_widget(
            Label(text="Categories")
        )

        for category in self.data.keys():

            btn = Button(text=category)

            btn.bind(
                on_press=lambda x,
                c=category:
                self.show_subcategories(c)
            )

            self.root_layout.add_widget(btn)

        cart_btn = Button(text="View Cart")

        cart_btn.bind(on_press=self.show_cart)

        self.root_layout.add_widget(cart_btn)

    # --------------------
    # Subcategories
    # --------------------

    def show_subcategories(self, category):

        self.root_layout.clear_widgets()

        self.root_layout.add_widget(
            Label(text=category)
        )

        for sub in self.data[category]:

            btn = Button(text=sub)

            btn.bind(
                on_press=lambda x,
                s=sub:
                self.show_products(category, s)
            )

            self.root_layout.add_widget(btn)

        back = Button(text="Back")

        back.bind(
            on_press=lambda x:
            self.show_categories()
        )

        self.root_layout.add_widget(back)

    # --------------------
    # Products
    # --------------------

    def show_products(self, category, subcategory):

        self.root_layout.clear_widgets()

        search = TextInput(
            hint_text="Search Product"
        )

        search.bind(
            text=lambda instance,
            value:
            self.search_products(
                value,
                category,
                subcategory
            )
        )

        self.root_layout.add_widget(search)

        scroll = ScrollView()

        grid = GridLayout(
            cols=2,
            spacing=10,
            padding=10,
            size_hint_y=None
        )

        grid.bind(
            minimum_height=grid.setter(
                "height"
            )
        )

        products = self.data[category][subcategory]

        for product in products:

            grid.add_widget(
                self.create_product_card(
                    product
                )
            )

        scroll.add_widget(grid)

        self.root_layout.add_widget(scroll)

        back = Button(text="Back")

        back.bind(
            on_press=lambda x:
            self.show_subcategories(category)
        )

        self.root_layout.add_widget(back)

    # --------------------
    # Product Card
    # --------------------

    def create_product_card(self, product):

        card = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=150
        )

        img = Image(
            source=product["image"]
        )

        info = BoxLayout(
            orientation="vertical"
        )

        name = Label(
            text=product["name"]
        )

        price = Label(
            text=f"KES {product['price']}"
        )

        add_btn = Button(
            text="Add To Cart"
        )

        add_btn.bind(
            on_press=lambda x,
            p=product:
            self.add_to_cart(p)
        )

        info.add_widget(name)
        info.add_widget(price)
        info.add_widget(add_btn)

        card.add_widget(img)
        card.add_widget(info)

        return card

    # --------------------
    # Cart
    # --------------------

    def add_to_cart(self, product):

        self.cart.append(product)

    def show_cart(self, instance=None):

        self.root_layout.clear_widgets()

        self.root_layout.add_widget(
            Label(text="Shopping Cart")
        )

        total = 0

        for item in self.cart:

            row = BoxLayout()

            row.add_widget(
                Label(
                    text=item["name"]
                )
            )

            row.add_widget(
                Label(
                    text=str(item["price"])
                )
            )

            remove = Button(
                text="Remove"
            )

            remove.bind(
                on_press=lambda x,
                i=item:
                self.remove_item(i)
            )

            row.add_widget(remove)

            self.root_layout.add_widget(row)

            total += item["price"]

        self.total_amount = total

        self.root_layout.add_widget(
            Label(
                text=f"Total KES {total}"
            )
        )

        checkout = Button(
            text="Proceed To Checkout"
        )

        checkout.bind(
            on_press=self.payment_options
        )

        self.root_layout.add_widget(checkout)

    def remove_item(self, item):

        if item in self.cart:

            self.cart.remove(item)

        self.show_cart()

    # --------------------
    # Search
    # --------------------

    def search_products(
        self,
        text,
        category,
        subcategory
    ):

        pass

    # --------------------
    # Payment Options
    # --------------------

    def payment_options(
        self,
        instance=None
    ):

        self.root_layout.clear_widgets()

        self.root_layout.add_widget(
            Label(
                text="Select Payment Method"
            )
        )

        whatsapp = Button(
            text="WhatsApp Checkout"
        )

        mpesa = Button(
            text="Lipa na M-Pesa"
        )

        paypal = Button(
            text="PayPal"
        )

        whatsapp.bind(
            on_press=self.checkout_whatsapp
        )

        mpesa.bind(
            on_press=self.mpesa_screen
        )

        paypal.bind(
            on_press=self.paypal_payment
        )

        self.root_layout.add_widget(
            whatsapp
        )

        self.root_layout.add_widget(
            mpesa
        )

        self.root_layout.add_widget(
            paypal
        )

    # --------------------
    # WhatsApp
    # --------------------

    def checkout_whatsapp(
        self,
        instance=None
    ):

        message = "Order Details:\n"

        total = 0

        for item in self.cart:

            message += (
                f"{item['name']} - "
                f"KES {item['price']}\n"
            )

            total += item["price"]

        message += f"\nTotal={total}"

        url = (
            f"https://wa.me/"
            f"{PHONE_NUMBER}"
            f"?text={message}"
        )

        webbrowser.open(url)

    # --------------------
    # M-Pesa
    # --------------------

    def mpesa_screen(
        self,
        instance=None
    ):

        self.root_layout.clear_widgets()

        self.phone_input = TextInput(
            hint_text="2547XXXXXXXX"
        )

        pay_btn = Button(
            text=f"Pay KES {self.total_amount}"
        )

        pay_btn.bind(
            on_press=self.send_stk_push
        )

        self.root_layout.add_widget(
            Label(text="M-Pesa Payment")
        )

        self.root_layout.add_widget(
            self.phone_input
        )

        self.root_layout.add_widget(
            pay_btn
        )

    def send_stk_push(
        self,
        instance=None
    ):

        phone = self.phone_input.text

        try:

            response = requests.post(
                f"{API_URL}/stkpush",
                json={
                    "phone": phone,
                    "amount": self.total_amount
                }
            )

            print(
                response.json()
            )

        except Exception as e:

            print(e)

    # --------------------
    # PayPal
    # --------------------

    def paypal_payment(
        self,
        instance=None
    ):

        try:

            response = requests.post(
                f"{API_URL}/paypal-order",
                json={
                    "amount":
                    self.total_amount
                }
            )

            data = response.json()

            webbrowser.open(
                data["approval_url"]
            )

        except Exception as e:

            print(e)


if __name__ == "__main__":
    ShopApp().run()