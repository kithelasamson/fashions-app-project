import json
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp

PHONE_NUMBER = "254757486132"  # <-- replace with your WhatsApp number


class ShopApp(App):

    def build(self):
        self.data = json.load(open("products.json"))
        self.cart = []

        self.root_layout = BoxLayout(orientation='vertical')
        self.show_categories()
        return self.root_layout

    # ---------------------------
    # CATEGORY SCREEN
    # ---------------------------
    def show_categories(self):
        self.root_layout.clear_widgets()

        self.root_layout.add_widget(Label(text="Categories", size_hint=(1, 0.1)))

        for category in self.data.keys():
            btn = Button(text=category, size_hint=(1, 0.1))
            btn.bind(on_press=lambda instance, c=category: self.show_subcategories(c))
            self.root_layout.add_widget(btn)

        cart_btn = Button(text="View Cart", size_hint=(1, 0.1))
        cart_btn.bind(on_press=self.show_cart)
        self.root_layout.add_widget(cart_btn)

    # ---------------------------
    # SUBCATEGORY SCREEN
    # ---------------------------
    def show_subcategories(self, category):
        self.root_layout.clear_widgets()

        self.root_layout.add_widget(Label(text=f"{category}", size_hint=(1, 0.1)))

        for sub in self.data[category].keys():
            btn = Button(text=sub, size_hint=(1, 0.1))
            btn.bind(on_press=lambda instance, s=sub: self.show_products(category, s))
            self.root_layout.add_widget(btn)

        back = Button(text="Back", size_hint=(1, 0.1))
        back.bind(on_press=lambda x: self.show_categories())
        self.root_layout.add_widget(back)

    # ---------------------------
    # PRODUCT SCREEN
    # ---------------------------
    def show_products(self, category, subcategory):
        self.root_layout.clear_widgets()

        # Search bar
        self.search_input = TextInput(
            hint_text="🔍 Search product...",
            size_hint=(1, 0.08),
            padding=10
        )
        self.search_input.bind(
            text=lambda instance, value: self.search_products(value, category, subcategory)
        )
        self.root_layout.add_widget(self.search_input)

        scroll = ScrollView()

        grid = GridLayout(
            cols=2,
            spacing=10,
            padding=10,
            size_hint_y=None
        )
        grid.bind(minimum_height=grid.setter('height'))

        products = self.data[category][subcategory]

        for product in products:
            grid.add_widget(self.create_product_card(product))

        scroll.add_widget(grid)
        self.root_layout.add_widget(scroll)

        back = Button(text="⬅ Back", size_hint=(1, 0.1))
        back.bind(on_press=lambda x: self.show_subcategories(category))
        self.root_layout.add_widget(back)

    # ---------------------------
    # CREATE PRODUCT CARD
    # ---------------------------
    def create_product_card(self, product):
        card = BoxLayout(size_hint_y=None, height=120)

        img = Image(source=product["image"])

        info = BoxLayout(orientation='vertical')

        name = Label(text=product["name"])
        price = Label(text=f"KES {product['price']}")

        btn = Button(text="Add to Cart")
        btn.bind(on_press=lambda instance, p=product: self.add_to_cart(p))

        info.add_widget(name)
        info.add_widget(price)
        info.add_widget(btn)

        card.add_widget(img)
        card.add_widget(info)

        return card

    # ---------------------------
    # ADD TO CART
    # ---------------------------
    def add_to_cart(self, product):
        self.cart.append(product)
        print("Added:", product["name"])

    # ---------------------------
    # CART SCREEN
    # ---------------------------
    def show_cart(self, instance=None):
        self.root_layout.clear_widgets()

        self.root_layout.add_widget(Label(text="Your Cart", size_hint=(1, 0.1)))

        total = 0

        for item in self.cart:
            box = BoxLayout(size_hint_y=None, height=80)

            name = Label(text=item["name"])
            price = Label(text=f"KES {item['price']}")

            remove_btn = Button(text="Remove")
            remove_btn.bind(on_press=lambda inst, i=item: self.remove_from_cart(i))

            box.add_widget(name)
            box.add_widget(price)
            box.add_widget(remove_btn)

            self.root_layout.add_widget(box)

            total += item["price"]

        self.root_layout.add_widget(Label(text=f"Total: KES {total}", size_hint=(1, 0.1)))

        checkout_btn = Button(text="Checkout via WhatsApp", size_hint=(1, 0.1))
        checkout_btn.bind(on_press=self.checkout)

        back_btn = Button(text="Back", size_hint=(1, 0.1))
        back_btn.bind(on_press=lambda x: self.show_categories())

        self.root_layout.add_widget(checkout_btn)
        self.root_layout.add_widget(back_btn)

    # ---------------------------
    # REMOVE FROM CART
    # ---------------------------
    def remove_from_cart(self, item):
        if item in self.cart:
            self.cart.remove(item)
            self.show_cart()

    # ---------------------------
    # SEARCH FUNCTION
    # ---------------------------
    def search_products(self, text, category, subcategory):
        self.root_layout.clear_widgets()

        self.root_layout.add_widget(Label(text="Search Results", size_hint=(1, 0.1)))

        filtered = [
            p for p in self.data[category][subcategory]
            if text.lower() in p["name"].lower()
        ]

        for product in filtered:
            self.root_layout.add_widget(self.create_product_card(product))

        back = Button(text="Back", size_hint=(1, 0.1))
        back.bind(on_press=lambda x: self.show_products(category, subcategory))
        self.root_layout.add_widget(back)

    # ---------------------------
    # WHATSAPP CHECKOUT
    # ---------------------------
    def checkout(self, instance=None):
        if not self.cart:
            return

        message = "Hello, I want to order:\n"
        total = 0

        for item in self.cart:
            message += f"- {item['name']} (KES {item['price']})\n"
            total += item["price"]

        message += f"\nTotal: KES {total}"

        url = f"https://wa.me/{PHONE_NUMBER}?text={message}"
        webbrowser.open(url)


ShopApp().run()