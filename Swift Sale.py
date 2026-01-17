import mysql.connector
import datetime
import io
import os
import random
import threading
import math
from functools import partial
from flask import Flask
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.carousel import Carousel
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle, Ellipse
from kivy.properties import StringProperty, ListProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.uix.spinner import Spinner
from kivy.uix.dropdown import DropDown

# try to import qrcode if installed
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

# database settings
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'SwiftSale_DB'
}

# helper to get connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    # connect to server first to create db
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        c = conn.cursor()
        c.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        return

    # connect to actual db and make tables
    conn = get_db_connection()
    c = conn.cursor()
    
    # users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            username VARCHAR(255) UNIQUE, 
            password VARCHAR(255), 
            role VARCHAR(50)
        )
    """)
    # products table
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            name VARCHAR(255), 
            category VARCHAR(100), 
            price DECIMAL(10, 2), 
            stock INT
        )
    """)
    # customers list
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            name VARCHAR(255), 
            phone VARCHAR(50), 
            email VARCHAR(255)
        )
    """)
    # sales history
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            date DATETIME, 
            total DECIMAL(10, 2), 
            customer_id INT, 
            qr_data TEXT
        )
    """)
    # items inside a sale
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales_items (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            sale_id INT, 
            product_id INT, 
            product_name VARCHAR(255), 
            qty INT, 
            price DECIMAL(10, 2),
            FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE
        )
    """)
    # payment records
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            sale_id INT, 
            method VARCHAR(50), 
            reference VARCHAR(255), 
            amount DECIMAL(10, 2), 
            timestamp DATETIME, 
            FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE
        )
    """)
    
    # add admin if empty
    c.execute("SELECT count(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", ('admin', '132009', 'admin'))
        
        # dummy data for testing
        items = [
            ('iPhone 15', 'Electronics', 79900, 20), ('MacBook Air M3', 'Electronics', 114900, 10), 
            ('iPad Pro 11"', 'Electronics', 81900, 15), ('Apple Watch Series 9', 'Electronics', 41900, 25),
            ('Sony WH-1000XM5', 'Electronics', 29990, 30), ('Samsung S24 Ultra', 'Electronics', 129999, 12),
            ('Coca Cola 500ml', 'Beverages', 40, 200), ('Pepsi 500ml', 'Beverages', 40, 180),
            ('Red Bull', 'Beverages', 125, 100), ('Monster Energy', 'Beverages', 110, 80),
            ('Bisleri Water 1L', 'Beverages', 20, 500), ('Tropicana Orange', 'Beverages', 110, 60),
            ('Real Apple Juice', 'Beverages', 120, 60), ('Lipton Ice Tea', 'Beverages', 55, 90),
            ('Lays Classic Salted', 'Snacks', 20, 200), ('Doritos Cheese', 'Snacks', 30, 150),
            ('Pringles Original', 'Snacks', 110, 80), ('Kurkure Masala', 'Snacks', 20, 180),
            ('Maggi 2-Minute', 'Snacks', 14, 300), ('Oreo Biscuits', 'Snacks', 35, 120),
            ('Dark Fantasy', 'Snacks', 40, 100), ('Haldiram Bhujia', 'Snacks', 55, 90),
            ('Snickers Bar', 'Snacks', 50, 200), ('KitKat 4-Finger', 'Snacks', 30, 220),
            ('Tata Salt 1kg', 'Grocery', 28, 100), ('Aashirvaad Atta 5kg', 'Grocery', 240, 50),
            ('Fortune Oil 1L', 'Grocery', 145, 60), ('India Gate Basmati', 'Grocery', 650, 40),
            ('Tur Dal 1kg', 'Grocery', 160, 45), ('Sugar 1kg', 'Grocery', 48, 80),
            ('Taj Mahal Tea 250g', 'Grocery', 180, 55), ('Nescafe Classic', 'Grocery', 220, 50),
            ('Dove Soap 3-Pack', 'Personal Care', 140, 60), ('Nivea Body Lotion', 'Personal Care', 250, 40),
            ('Colgate MaxFresh', 'Personal Care', 90, 80), ('Oral-B Toothbrush', 'Personal Care', 40, 100),
            ('Loreal Shampoo', 'Personal Care', 320, 35), ('Gillette Mach3', 'Personal Care', 350, 45),
            ('Old Spice Deodorant', 'Personal Care', 220, 50), ('Dettol Handwash', 'Personal Care', 75, 70),
            ('Classmate Notebook', 'Stationery', 60, 150), ('Pilot V5 Pen', 'Stationery', 50, 200),
            ('Parker Vector Pen', 'Stationery', 350, 30), ('Camlin Pencils 10s', 'Stationery', 40, 120),
            ('Fevicol 100g', 'Stationery', 35, 100), ('Scotch Tape', 'Stationery', 45, 80),
            ('Surf Excel 1kg', 'Household', 160, 60), ('Vim Dish Bar', 'Household', 30, 150),
            ('Lizol Floor Cleaner', 'Household', 180, 40), ('Harpic Cleaner', 'Household', 95, 55),
            ('Duracell AA 4x', 'Household', 140, 80), ('Odonil Air Freshener', 'Household', 65, 70),
            ('Scotch Brite', 'Household', 25, 120), ('Garbage Bags', 'Household', 90, 65)
        ] * 3 
        
        unique_items = []
        for i, item in enumerate(items):
            suffix = "" if i < 60 else (f" (V{i//60})")
            unique_items.append((item[0] + suffix, item[1], item[2], item[3]))
        
        c.executemany("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", unique_items)

        # random names for demo customers
        f_names = ["Aarav", "Arjun", "Aditya", "Vihaan", "Rohan", "Rahul", "Vikram", "Suresh", "Riya", "Diya", "Ananya", "Ishita", "Kavya", "Priya", "Pooja", "Neha", "Sneha", "Amit", "Manish", "Raj", "Kartik", "Sanjay", "Deepak", "Anil", "Meera", "Sunita", "Anita"]
        l_names = ["Sharma", "Verma", "Gupta", "Singh", "Patel", "Kumar", "Yadav", "Mishra", "Reddy", "Jain", "Mehta", "Malhotra", "Saxena", "Chopra", "Deshmukh", "Nair", "Iyer", "Rao", "Gowda", "Bhat"]
        
        for i in range(45):
            fn = random.choice(f_names)
            ln = random.choice(l_names)
            phone = f"+91 {random.randint(6000, 9999)} {random.randint(10000, 99999)}"
            email = f"{fn.lower()}.{ln.lower()}@gmail.com"
            c.execute("INSERT INTO customers (name, phone, email) VALUES (%s, %s, %s)", (f"{fn} {ln}", phone, email))

    conn.commit()
    conn.close()

# flask app to serve bills
app_server = Flask(__name__)

@app_server.route('/bill/<int:sale_id>')
def serve_bill(sale_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # fetch sale info
        c.execute("SELECT date, total FROM sales WHERE id=%s", (sale_id,))
        sale = c.fetchone()
        if not sale: return "<h1>Receipt Not Found</h1>"
        
        # fetch items in sale
        c.execute("SELECT product_name, qty, price FROM sales_items WHERE sale_id=%s", (sale_id,))
        items = c.fetchall()
        conn.close()
        
        # build html receipt
        html = f"""
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
              body {{ font-family: -apple-system, sans-serif; padding: 20px; background: #F2F2F7; }}
              .card {{ background: white; padding: 30px; border-radius: 18px; max-width: 400px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
              h1 {{ font-size: 24px; text-align: center; color: #1C1C1E; margin-bottom: 5px; }}
              .meta {{ text-align: center; color: #8E8E93; font-size: 14px; margin-bottom: 20px; }}
              .line {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #E5E5EA; color: #1C1C1E; }}
              .total {{ font-weight: 700; font-size: 20px; margin-top: 20px; display: flex; justify-content: space-between; color: #000000; }}
            </style>
          </head>
          <body>
            <div class="card">
              <h1>SwiftSale Receipt</h1>
              <div class="meta">{sale[0]} • #{sale_id}</div>
        """
        for i in items:
            html += f'<div class="line"><span>{i[0]} <small>x{i[1]}</small></span> <span>{i[2]*i[1]:.2f}</span></div>'
        
        html += f"""
              <div class="total"><span>Total</span> <span>Rs {sale[1]:,.2f}</span></div>
            </div>
          </body>
        </html>
        """
        return html
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

# run flask in background thread
def run_flask():
    try:
        app_server.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
    except:
        pass

threading.Thread(target=run_flask, daemon=True).start()

# kivy widgets setup
class ListGroup(BoxLayout):
    pass

class ListRow(BoxLayout):
    main_text = StringProperty("")
    sub_text = StringProperty("")
    value_text = StringProperty("")
    is_last = BooleanProperty(False)

class CartItem(BoxLayout):
    name = StringProperty()
    qty = StringProperty()
    price = StringProperty()
    delete_fn = ObjectProperty()

class DiscountSelect(BoxLayout):
    controller = ObjectProperty(None)

# drawing icons with code
class SVGIcon(Widget):
    icon_type = StringProperty('default')
    color = ListProperty([0.5, 0.5, 0.55, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        w, h = self.width, self.height
        s = min(w, h) * 0.04 
        with self.canvas:
            Color(*self.color)
            width = dp(1.3)
            # draw specific shape based on type
            if self.icon_type == 'settings':
                Line(circle=(cx, cy, 6*s), width=width)
                for i in range(0, 360, 45):
                    Line(points=[cx + math.cos(math.radians(i))*(14*s), cy + math.sin(math.radians(i))*(14*s), cx + math.cos(math.radians(i))*(9*s), cy + math.sin(math.radians(i))*(9*s)], width=width*1.5)
            elif self.icon_type in ('pos', 'sales'): 
                ox, oy = cx, cy - 2*s
                Line(points=[ox-6*s, oy+14*s, ox-6*s, oy+20*s, ox+6*s, oy+20*s, ox+6*s, oy+14*s], width=width)
                Line(rounded_rectangle=(ox-12*s, oy-12*s, 24*s, 26*s, 4*s), width=width)
                Line(circle=(ox, oy-2*s, 2*s), width=width)
            elif self.icon_type in ('inventory', 'stock'):
                ox, oy = cx, cy
                Line(points=[ox, oy, ox, oy-10*s], width=width)
                Line(points=[ox, oy, ox-10*s, oy+6*s], width=width)
                Line(points=[ox, oy, ox+10*s, oy+6*s], width=width)
                Line(points=[ox-10*s, oy+6*s, ox, oy+12*s, ox+10*s, oy+6*s, ox+10*s, oy-6*s, ox, oy-12*s, ox-10*s, oy-6*s], width=width, joint='round')
            elif self.icon_type == 'customers':
                ox, oy = cx, cy
                Line(circle=(ox, oy+6*s, 5*s), width=width)
                Line(ellipse=(ox-10*s, oy-12*s, 20*s, 14*s, 0, 180), width=width)
            elif self.icon_type in ('reports', 'monthly'):
                ox, oy = cx - 10*s, cy - 10*s
                Line(rounded_rectangle=(ox, oy, 6*s, 10*s, 1), width=width)
                Line(rounded_rectangle=(ox+7*s, oy, 6*s, 20*s, 1), width=width)
                Line(rounded_rectangle=(ox+14*s, oy, 6*s, 15*s, 1), width=width)
            elif self.icon_type in ('products', 'top_product'):
                ox, oy = cx, cy
                Line(points=[ox-8*s, oy, ox, oy+10*s, ox+12*s, oy+10*s, ox+12*s, oy-10*s, ox-8*s, oy-10*s, ox-8*s, oy, ox-16*s, oy], width=width)
                Line(circle=(ox-8*s, oy, 2*s), width=width)
            elif self.icon_type == 'dues':
                ox, oy = cx, cy
                Line(rounded_rectangle=(ox-12*s, oy-8*s, 24*s, 16*s, 3*s), width=width)
                Line(points=[ox-12*s, oy+2*s, ox+12*s, oy+2*s], width=width)
                Line(points=[ox-8*s, oy-4*s, ox, oy-4*s], width=width)
            else:
                Line(circle=(cx, cy, 5*s), width=width)

class AutocompleteInput(TextInput):
    suggestions = ListProperty([])
    dropdown = ObjectProperty(None)
    is_selecting = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dropdown = DropDown()
        self.bind(text=self.on_text_change)
        # default text input styling
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (1, 1, 1, 1)
        self.foreground_color = (0, 0, 0, 1)
        self.hint_text_color = (0.5, 0.5, 0.55, 1) 
        self.padding = [dp(12), dp(12)]
        self.multiline = False
        self.cursor_color = (0, 0.47, 1, 1) 

    def on_text_change(self, instance, value):
        if self.is_selecting: return
        if len(value) < 2:
            if self.dropdown.parent: self.dropdown.dismiss()
            return
        try:
            conn = get_db_connection()
            c = conn.cursor()
            # find matches
            c.execute("SELECT DISTINCT name FROM products WHERE name LIKE %s LIMIT 5", (f"%{value}%",))
            results = [r[0] for r in c.fetchall()]
            conn.close()
            
            # update dropdown
            self.dropdown.clear_widgets()
            if results:
                for name in results:
                    btn = Button(text=name, size_hint_y=None, height=dp(44), 
                               background_color=get_color_from_hex('#FFFFFF'), 
                               background_normal='',
                               color=get_color_from_hex('#1D1D1F'),
                               halign='left', padding_x=dp(15))
                    btn.bind(size=btn.setter('text_size')) 
                    btn.bind(on_release=lambda btn: self.select_suggestion(btn.text))
                    self.dropdown.add_widget(btn)
                if not self.dropdown.parent: self.dropdown.open(self)
            else:
                if self.dropdown.parent: self.dropdown.dismiss()
        except mysql.connector.Error:
            pass

    def select_suggestion(self, text):
        self.is_selecting = True
        self.text = text
        self.dropdown.dismiss()
        # reset selection flag shortly after
        Clock.schedule_once(lambda dt: setattr(self, 'is_selecting', False), 0.1)

# simple stats card
class StatSlide(BoxLayout):
    title = StringProperty("")
    value = StringProperty("")
    icon = StringProperty("default")
    color = ListProperty([0, 0, 0, 1])

# main menu card
class ModernCard(BoxLayout):
    main_text = StringProperty("")
    sub_text = StringProperty("")
    side_text = StringProperty("")
    side_color = ListProperty([0.9, 0.96, 0.92, 1]) 
    side_text_color = ListProperty([0.07, 0.45, 0.2, 1]) 

KV = """
#:import hex kivy.utils.get_color_from_hex

<StyledInput@TextInput>:
    background_normal: ''
    background_active: ''
    background_color: hex('#FFFFFF')
    foreground_color: hex('#000000')
    hint_text_color: hex('#8E8E93')
    multiline: False
    font_size: sp(17)
    size_hint_y: None
    height: dp(50)
    padding: [dp(16), dp(15)]
    cursor_color: hex('#007AFF')
    canvas.before:
        Color:
            rgba: self.background_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]
        Color:
            rgba: hex('#C6C6C8')
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(10))
            width: 1

<PrimaryButton@Button>:
    background_normal: ''
    background_color: hex('#007AFF')
    color: 1,1,1,1
    bold: True
    font_size: sp(17)
    size_hint_y: None
    height: dp(52)
    canvas.before:
        Color:
            rgba: self.background_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

<ListGroup>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: 0
    spacing: 0
    canvas.before:
        Color:
            rgba: hex('#FFFFFF')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

<ListRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(52)
    padding: [dp(16), 0]
    spacing: dp(10)
    canvas.after:
        Color:
            rgba: (hex('#E5E5EA') if not self.is_last else [0,0,0,0])
        Line:
            points: [self.x + dp(16), self.y, self.right, self.y]
            width: 1

    BoxLayout:
        orientation: 'vertical'
        valign: 'middle'
        Label:
            text: root.main_text
            color: hex('#000000')
            font_size: sp(17)
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Label:
            text: root.sub_text
            color: hex('#8E8E93')
            font_size: sp(13)
            text_size: self.size
            halign: 'left'
            valign: 'top'
            size_hint_y: None
            height: dp(16) if root.sub_text else 0
            opacity: 1 if root.sub_text else 0

    Label:
        text: root.value_text
        color: hex('#8E8E93')
        font_size: sp(17)
        text_size: self.size
        halign: 'right'
        valign: 'middle'
        size_hint_x: 0.45
        shorten: True
        markup: True
        shorten_from: 'right'

<DiscountSelect>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(40)
    spacing: dp(8)
    Button:
        text: "0%"
        background_normal: ''
        background_color: hex('#E5E5EA')
        color: hex('#000000')
        on_release: if root.controller: root.controller.set_discount(0)
    Button:
        text: "5%"
        background_normal: ''
        background_color: hex('#E5E5EA')
        color: hex('#000000')
        on_release: if root.controller: root.controller.set_discount(0.05)
    Button:
        text: "10%"
        background_normal: ''
        background_color: hex('#E5E5EA')
        color: hex('#000000')
        on_release: if root.controller: root.controller.set_discount(0.10)
    Button:
        text: "15%"
        background_normal: ''
        background_color: hex('#E5E5EA')
        color: hex('#000000')
        on_release: if root.controller: root.controller.set_discount(0.15)

<StatSlide>:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]
        Color:
            rgba: 0, 0, 0, 0.05
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(18))
            width: 1
    SVGIcon:
        icon_type: root.icon
        color: root.color
        size_hint_y: 0.45
        pos_hint: {'center_x': 0.5}
    Label:
        text: root.title
        color: hex('#8E8E93')
        font_size: sp(13)
        bold: True
    Label:
        text: root.value
        color: hex('#1C1C1E')
        font_size: sp(26)
        bold: True

<MenuCard@Button>:
    title: ''
    icon_type: 'default'
    background_color: 0,0,0,0
    background_normal: ''
    size_hint_y: None
    height: dp(140)
    canvas.before:
        Color:
            rgba: hex('#FFFFFF')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(12)
        pos: root.pos
        size: root.size
        SVGIcon:
            icon_type: root.icon_type
            size_hint_y: 0.6
            pos_hint: {'center_x': 0.5}
            color: hex('#007AFF')
        Label:
            text: root.title
            color: hex('#1C1C1E')
            bold: True
            font_size: sp(15)
            size_hint_y: 0.4
            text_size: self.size
            halign: 'center'
            valign: 'top'

<StatusPill@Label>:
    background_color: [0,0,0,0]
    color: [0,0,0,1]
    font_size: sp(13)
    bold: True
    canvas.before:
        Color:
            rgba: root.background_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]

<ModernCard>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(85)
    padding: [dp(20), dp(10)]
    spacing: dp(15)
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
            
    BoxLayout:
        orientation: 'vertical'
        valign: 'middle'
        spacing: dp(4)
        Label:
            text: root.main_text
            color: hex('#1C1C1E')
            font_size: sp(17)
            text_size: self.size
            halign: 'left'
            valign: 'bottom'
            bold: True
        Label:
            text: root.sub_text
            color: hex('#8E8E93')
            font_size: sp(14)
            text_size: self.size
            halign: 'left'
            valign: 'top'
    
    AnchorLayout:
        anchor_x: 'right'
        anchor_y: 'center'
        size_hint_x: 0.45
        StatusPill:
            text: root.side_text
            color: root.side_text_color
            background_color: root.side_color
            size_hint: None, None
            size: self.texture_size[0] + dp(24), dp(30)
            halign: 'center'
            valign: 'middle'

<CartItem@BoxLayout>:
    name: ''
    qty: ''
    price: ''
    delete_fn: None
    size_hint_y: None
    height: dp(60)
    canvas.before:
        Color:
            rgba: hex('#FFFFFF')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]
    padding: dp(15)
    BoxLayout:
        orientation: 'vertical'
        Label:
            text: root.name
            color: hex('#1B2559')
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            bold: True
            font_size: sp(15)
        Label:
            text: root.qty + "  |  " + root.price
            color: hex('#A3AED0')
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            font_size: sp(13)
    Button:
        text: "Delete"
        color: hex('#FF3B30')
        background_color: 0,0,0,0
        size_hint_x: 0.3
        font_size: sp(14)
        on_release: root.delete_fn()

<LoginScreen>:
    canvas.before:
        Color:
            rgba: hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size
    FloatLayout:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(35)
            spacing: dp(25)
            size_hint: 0.9, 0.65
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            canvas.before:
                Color:
                    rgba: hex('#FFFFFF')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(24)]
            
            Label:
                text: "SwiftSale"
                font_size: sp(36)
                bold: True
                color: hex('#007AFF')
                size_hint_y: 0.3
            StyledInput:
                id: user
                hint_text: "Username"
                text: "admin"
            StyledInput:
                id: pwd
                hint_text: "Password"
                password: True
                text: "132009"
            PrimaryButton:
                text: "Sign In"
                on_release: root.do_login()
            Label:
                id: err
                text: ""
                color: hex('#FF3B30')
                font_size: sp(14)
                size_hint_y: None
                height: dp(30)

<DashboardScreen>:
    canvas.before:
        Color:
            rgba: hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: [dp(20), dp(20)]
        spacing: dp(20)
        
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            Label:
                text: "Dashboard"
                color: hex('#1C1C1E')
                bold: True
                font_size: sp(32)
                halign: 'left'
                text_size: self.size
            Button:
                text: "Logout"
                size_hint_x: None
                width: dp(85)
                height: dp(36)
                pos_hint: {'center_y': 0.5}
                background_normal: ''
                background_color: 0,0,0,0
                color: hex('#007AFF')
                font_size: sp(17)
                on_release: app.root.current = 'login'

        BoxLayout:
            size_hint_y: None
            height: dp(160)
            Carousel:
                id: stats_carousel
                direction: 'right'
                loop: True

        ScrollView:
            size_hint_y: 1
            GridLayout:
                cols: 2
                spacing: dp(15)
                padding: [0, dp(5), 0, dp(5)]
                size_hint_y: None
                height: self.minimum_height
                
                MenuCard:
                    title: "New Sale"
                    icon_type: "pos"
                    on_release: app.root.current = 'pos'
                MenuCard:
                    title: "Inventory"
                    icon_type: "inventory"
                    on_release: app.root.current = 'inventory'
                MenuCard:
                    title: "Customers"
                    icon_type: "customers"
                    on_release: app.root.current = 'customers'
                MenuCard:
                    title: "Reports"
                    icon_type: "reports"
                    on_release: app.root.current = 'reports'
                MenuCard:
                    title: "Products"
                    icon_type: "products"
                    on_release: app.root.current = 'database'
                MenuCard:
                    title: "Preferences"
                    icon_type: "settings"
                    on_release: app.root.current = 'settings'

<POSScreen>:
    canvas.before:
        Color:
            rgba: hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: hex('#F9F9F9')
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "Done"
                size_hint_x: None
                width: dp(70)
                background_color: 0,0,0,0
                color: hex('#007AFF')
                font_size: sp(17)
                on_release: app.root.current = 'dashboard'
            Label:
                text: "New Sale"
                color: hex('#1C1C1E')
                bold: True
                font_size: sp(18)
                halign: 'center'
                text_size: self.size
            Widget: 
                size_hint_x: None
                width: dp(70)

        BoxLayout:
            orientation: 'vertical'
            padding: dp(20)
            spacing: dp(15)
            
            StyledInput:
                id: cust_search
                hint_text: "Find Customer (Name/Phone)"
            Label:
                id: cust_pref_label
                text: ""
                size_hint_y: None
                height: dp(20)
                color: hex('#34C759')
                font_size: sp(13)
                bold: True

            BoxLayout:
                size_hint_y: None
                height: dp(50)
                spacing: dp(12)
                AutocompleteInput:
                    id: prod_inp
                    hint_text: "Search Product"
                    size_hint_x: 0.6
                    foreground_color: hex('#000000')
                    hint_text_color: hex('#3C3C43')
                    canvas.before:
                        Color:
                            rgba: hex('#FFFFFF')
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(10)]
                        Color:
                            rgba: hex('#C6C6C8')
                        Line:
                            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(10))
                            width: 1

                StyledInput:
                    id: qty_inp
                    hint_text: "Qty"
                    size_hint_x: 0.2
                    text: "0"
                    input_filter: 'int'
                PrimaryButton:
                    text: "Add"
                    size_hint_x: 0.2
                    on_release: root.add_item()
            
            ScrollView:
                canvas.before:
                    Color:
                        rgba: hex('#F2F2F7')
                    Rectangle:
                        pos: self.pos
                        size: self.size
                BoxLayout:
                    id: cart_list
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: [0, dp(10)]
                    spacing: dp(10)

        BoxLayout:
            size_hint_y: None
            height: dp(80)
            padding: [dp(20), dp(10)]
            spacing: dp(15)
            canvas.before:
                Color:
                    rgba: hex('#FFFFFF')
                Rectangle:
                    pos: self.pos
                    size: self.size
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                Label:
                    text: "Total Due"
                    color: hex('#8E8E93')
                    font_size: sp(16)
                    halign: 'left'
                    text_size: self.size
                Label:
                    id: total_lbl
                    text: "Rs 0.00"
                    bold: True
                    color: hex('#1C1C1E')
                    font_size: sp(22)
                    halign: 'right'
                    text_size: self.size
            PrimaryButton:
                text: "Charge"
                background_color: hex('#34C759')
                on_release: root.open_payment_modal()

<InventoryScreen>:
    canvas.before:
        Color:
            rgba: hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: hex('#F9F9F9')
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "Back"
                size_hint_x: None
                width: dp(70)
                background_color: 0,0,0,0
                color: hex('#007AFF')
                font_size: sp(17)
                on_release: app.root.current='dashboard'
            Label:
                text: "Inventory"
                color: hex('#1C1C1E')
                bold: True
                font_size: sp(17)
                halign: 'center'
                text_size: self.size
            Widget:
                size_hint_x: None
                width: dp(70)

        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                spacing: dp(20)
                padding: dp(20)
                size_hint_y: None
                height: self.minimum_height
                
                ListGroup:
                    height: dp(270)
                    padding: dp(20)
                    spacing: dp(15)
                    
                    Label:
                        text: "Edit Item"
                        font_size: sp(22)
                        bold: True
                        color: hex('#1C1C1E')
                        size_hint_y: None
                        height: dp(30)
                        halign: 'left'
                        text_size: self.size

                    StyledInput:
                        id: p_name
                        hint_text: "Product Name"
                    Spinner:
                        id: p_cat
                        text: "Select Category"
                        values: ('Electronics', 'Dairy', 'Beverages', 'Grocery', 'Snacks', 'Chocolates', 'Personal Care', 'Household', 'Baby Care', 'Stationery')
                        size_hint_y: None
                        height: dp(50)
                        background_normal: ''
                        background_color: hex('#FFFFFF')
                        color: hex('#1B2559')
                        canvas.before:
                            Color:
                                rgba: hex('#FFFFFF')
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [dp(10)]
                            Color:
                                rgba: hex('#C6C6C8')
                            Line:
                                rounded_rectangle: (self.x, self.y, self.width, self.height, dp(10))
                                width: 1
                    GridLayout:
                        cols: 2
                        spacing: dp(10)
                        size_hint_y: None
                        height: dp(50)
                        StyledInput:
                            id: p_price
                            hint_text: "Price (INR)"
                            input_filter: 'float'
                        StyledInput:
                            id: p_stock
                            hint_text: "Stock Qty"
                            input_filter: 'int'
                            
                PrimaryButton:
                    text: "Save Product"
                    on_release: root.upsert()
                Label:
                    id: status
                    text: ""
                    color: hex('#05CD99')
                    size_hint_y: None
                    height: dp(20)
                    font_size: sp(12)

<ReportScreen>:
    canvas.before:
        Color:
            rgba: hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: hex('#F9F9F9')
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "Back"
                size_hint_x: None
                width: dp(70)
                background_color: 0,0,0,0
                color: hex('#007AFF')
                font_size: sp(17)
                on_release: app.root.current = 'dashboard'
            Label:
                text: "Analytics"
                color: hex('#1C1C1E')
                bold: True
                font_size: sp(17)
                halign: 'center'
                text_size: self.size
            Widget:
                size_hint_x: None
                width: dp(70)
        
        BoxLayout:
            size_hint_y: None
            height: dp(70)
            padding: [dp(20), dp(10)]
            Spinner:
                id: report_type
                text: "Payment Methods"
                values: ("Payment Methods", "Sales by Category", "Top Products", "Daily Sales")
                size_hint_y: None
                height: dp(50)
                background_normal: ''
                background_color: hex('#FFFFFF')
                color: hex('#007AFF')
                bold: True
                on_text: root.generate_report()
                canvas.before:
                    Color:
                        rgba: hex('#FFFFFF')
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(10)]

        Label:
            id: report_title
            text: "Breakdown"
            color: hex('#8E8E93')
            bold: True
            font_size: sp(13)
            size_hint_y: None
            height: dp(30)
            halign: 'left'
            padding_x: dp(20)
            text_size: self.size
            
        ScrollView:
            BoxLayout:
                id: report_area
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: dp(20)
                spacing: dp(15)

<DatabaseScreen>:
    canvas.before:
        Color:
            rgba: hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: hex('#F9F9F9')
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "Back"
                size_hint_x: None
                width: dp(70)
                background_color: 0,0,0,0
                color: hex('#007AFF')
                font_size: sp(17)
                on_release: app.root.current='dashboard'
            Label:
                text: "Product Database"
                color: hex('#1C1C1E')
                bold: True
                font_size: sp(17)
                halign: 'center'
                text_size: self.size
            Widget:
                size_hint_x: None
                width: dp(70)
        
        BoxLayout:
            size_hint_y: None
            height: dp(70)
            padding: [dp(20), dp(10)]
            StyledInput:
                id: search_box
                hint_text: "Filter products..."
                on_text: root.on_search(self, self.text)

        ScrollView:
            canvas.before:
                Color:
                    rgba: hex('#F2F2F7')
                Rectangle:
                    pos: self.pos
                    size: self.size
            BoxLayout:
                id: db_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: [dp(20), dp(10), dp(20), dp(40)]
                spacing: dp(15)

<CustomerScreen>:
    canvas.before:
        Color:
            rgba: hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: hex('#F9F9F9')
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "Back"
                size_hint_x: None
                width: dp(70)
                background_color: 0,0,0,0
                color: hex('#007AFF')
                font_size: sp(17)
                on_release: app.root.current='dashboard'
            Label:
                text: "Directory"
                color: hex('#1C1C1E')
                bold: True
                font_size: sp(17)
                halign: 'center'
                text_size: self.size
            Widget:
                size_hint_x: None
                width: dp(70)
        
        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(25)
                padding: dp(20)
                
                ListGroup:
                    height: dp(250)
                    padding: dp(20)
                    spacing: dp(15)
                    
                    Label:
                        text: "Add New Contact"
                        font_size: sp(20)
                        bold: True
                        color: hex('#1C1C1E')
                        size_hint_y: None
                        height: dp(30)
                        halign: 'left'
                        text_size: self.size

                    StyledInput:
                        id: c_name
                        hint_text: "Full Name"
                    StyledInput:
                        id: c_phone
                        hint_text: "Phone Number"
                        input_filter: 'int'
                    StyledInput:
                        id: c_email
                        hint_text: "Email Address"
                
                PrimaryButton:
                    text: "Save Contact"
                    on_release: root.add_customer()
                Label:
                    id: status
                    text: ""
                    color: hex('#05CD99')
                    size_hint_y: None
                    height: dp(20)
                    font_size: sp(12)
                
                Label:
                    text: "All Contacts"
                    color: hex('#8E8E93')
                    bold: True
                    font_size: sp(14)
                    size_hint_y: None
                    height: dp(30)
                    halign: 'left'
                    text_size: self.size
                    padding_x: dp(10)
                
                BoxLayout:
                    id: cust_list
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(15)

<SettingsScreen>:
    canvas.before:
        Color:
            rgba: hex('#F2F2F7')
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: hex('#F9F9F9')
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "Back"
                size_hint_x: None
                width: dp(70)
                background_color: 0,0,0,0
                color: hex('#007AFF')
                font_size: sp(17)
                on_release: app.root.current='dashboard'
            Label:
                text: "Preferences"
                color: hex('#1C1C1E')
                bold: True
                font_size: sp(17)
                halign: 'center'
                text_size: self.size
            Widget:
                size_hint_x: None
                width: dp(70)

        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(15)
                padding: dp(20)
                
                ListGroup:
                    Button:
                        text: "Backup Database"
                        size_hint_y: None
                        height: dp(52)
                        background_normal: ''
                        background_color: 0,0,0,0
                        color: hex('#007AFF')
                        font_size: sp(17)
                        on_release: root.backup_db()
                    
                    Widget:
                        size_hint_y: None
                        height: 1
                        canvas:
                            Color:
                                rgba: hex('#C6C6C8')
                            Rectangle:
                                pos: self.x + dp(16), self.y
                                size: self.width - dp(16), 1

                    Button:
                        text: "Export Sales Data"
                        size_hint_y: None
                        height: dp(52)
                        background_normal: ''
                        background_color: 0,0,0,0
                        color: hex('#007AFF')
                        font_size: sp(17)
                        on_release: root.export_csv()

                    Widget:
                        size_hint_y: None
                        height: 1
                        canvas:
                            Color:
                                rgba: hex('#C6C6C8')
                            Rectangle:
                                pos: self.x + dp(16), self.y
                                size: self.width - dp(16), 1

                    Button:
                        text: "About"
                        size_hint_y: None
                        height: dp(52)
                        background_normal: ''
                        background_color: 0,0,0,0
                        color: hex('#007AFF')
                        font_size: sp(17)
                        on_release: root.show_about()
                
                Label:
                    id: status_label
                    text: ""
                    color: hex('#8E8E93')
                    size_hint_y: None
                    height: dp(30)
                    font_size: sp(13)
                    halign: 'center'
                    text_size: self.size
"""

Builder.load_string(KV)

class LoginScreen(Screen):
    def do_login(self):
        u = self.ids.user.text.strip()
        p = self.ids.pwd.text.strip()
        try:
            conn = get_db_connection()
            c = conn.cursor()
            # check credentials
            c.execute("SELECT role FROM users WHERE username=%s AND password=%s", (u, p))
            res = c.fetchone()
            conn.close()
            if res:
                self.manager.current = 'dashboard'
                self.ids.err.text = ""
            else:
                self.ids.err.text = "Invalid credentials"
        except mysql.connector.Error as e:
            self.ids.err.text = "DB Connection Error"

class DashboardScreen(Screen):
    def on_enter(self):
        self.update_stats()

    def update_stats(self):
        self.ids.stats_carousel.clear_widgets()
        try:
            conn = get_db_connection()
            c = conn.cursor()
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            month = datetime.datetime.now().strftime("%Y-%m")
            
            # calculate today's total
            c.execute("SELECT sum(total) FROM sales WHERE date LIKE %s", (f"{today}%",))
            today_val = c.fetchone()[0] or 0
            self.ids.stats_carousel.add_widget(StatSlide(
                title="Today", value=f"Rs {today_val:,.0f}",
                icon="sales", color=get_color_from_hex('#34C759')))

            # calculate month's total
            c.execute("SELECT sum(total) FROM sales WHERE date LIKE %s", (f"{month}%",))
            month_val = c.fetchone()[0] or 0
            self.ids.stats_carousel.add_widget(StatSlide(
                title="This Month", value=f"Rs {month_val:,.0f}",
                icon="monthly", color=get_color_from_hex('#007AFF')))

            # check for low stock items
            c.execute("SELECT count(*) FROM products WHERE stock < 20")
            low_stock = c.fetchone()[0]
            self.ids.stats_carousel.add_widget(StatSlide(
                title="Restock Needed", value=f"{low_stock} items",
                icon="stock", color=get_color_from_hex('#FF3B30')))

            # calculate pending dues
            c.execute("SELECT sum(total) FROM sales")
            total_sales = c.fetchone()[0] or 0
            c.execute("SELECT sum(amount) FROM payments")
            total_paid = c.fetchone()[0] or 0
            dues = total_sales - total_paid
            if dues < 1: dues = 0 
            self.ids.stats_carousel.add_widget(StatSlide(
                title="Pending Dues", value=f"Rs {dues:,.0f}",
                icon="dues", color=get_color_from_hex('#FF9500')))

            # find best selling product
            c.execute("SELECT product_name FROM sales_items GROUP BY product_name ORDER BY SUM(qty) DESC LIMIT 1")
            top = c.fetchone()
            top_name = top[0] if top else "N/A"
            if len(top_name) > 18: top_name = top_name[:16] + ".."
            self.ids.stats_carousel.add_widget(StatSlide(
                title="Top Performer", value=top_name,
                icon="top_product", color=get_color_from_hex('#5856D6')))

            conn.close()
        except mysql.connector.Error:
            pass

class POSScreen(Screen):
    cart = ListProperty([])
    selected_customer_id = NumericProperty(0)

    def on_enter(self):
        self.ids.cust_search.bind(text=self.on_customer_search)

    def on_customer_search(self, instance, value):
        if len(value) < 2:
            self.selected_customer_id = 0
            self.ids.cust_pref_label.text = ""
            return
        try:
            conn = get_db_connection()
            c = conn.cursor()
            # find customer by name or phone
            c.execute("""SELECT c.id, c.name FROM customers c WHERE c.name LIKE %s OR c.phone LIKE %s LIMIT 1""", (f"%{value}%", f"%{value}%"))
            result = c.fetchone()
            conn.close()
            if result:
                self.selected_customer_id = result[0]
                self.ids.cust_pref_label.text = f"Matched: {result[1]}"
        except mysql.connector.Error:
            pass

    def add_item(self):
        q = self.ids.prod_inp.text.strip()
        try: qty = int(self.ids.qty_inp.text.strip())
        except ValueError: qty = 0 
        if qty <= 0 or not q: return

        try:
            conn = get_db_connection()
            c = conn.cursor()
            # find product
            c.execute("SELECT * FROM products WHERE name LIKE %s", (f"%{q}%",))
            prod = c.fetchone()
            conn.close()

            if prod:
                # check if already in cart
                found = False
                for item in self.cart:
                    if item['id'] == prod[0]:
                        item['qty'] += qty
                        found = True
                        break
                if not found:
                    self.cart.append({'id': prod[0], 'name': prod[1], 'price': prod[3], 'qty': qty})
                self.refresh_cart()
                self.ids.prod_inp.text = ""
                self.ids.qty_inp.text = "0"
        except mysql.connector.Error:
            pass

    def refresh_cart(self):
        self.ids.cart_list.clear_widgets()
        total = 0
        for i, item in enumerate(self.cart):
            # create ui row for item
            w = CartItem(name=item['name'], qty=f"{item['qty']}", 
                        price=f"Rs {item['price']*item['qty']:.0f}")
            w.delete_fn = partial(self.remove_item, i)
            self.ids.cart_list.add_widget(w)
            total += item['price'] * item['qty']
        self.ids.total_lbl.text = f"Rs {total:,.2f}"

    def remove_item(self, idx):
        if 0 <= idx < len(self.cart):
            del self.cart[idx]
            self.refresh_cart()

    def open_payment_modal(self):
        if not self.cart: return
        # parse current total
        total = float(self.ids.total_lbl.text.replace('Rs ','').replace(',',''))
        modal = SplitPaymentModal(total_due=total, 
                                 customer_id=self.selected_customer_id,
                                 cart_items=self.cart.copy(),
                                 callback=self.on_payment_complete)
        modal.open()

    def on_payment_complete(self, sale_id):
        # reset cart after sale
        self.cart = []
        self.refresh_cart()
        self.ids.cust_search.text = ""
        self.show_qr_receipt(sale_id)

    def show_qr_receipt(self, sale_id):
        qr_screen = QRReceiptPopup(sale_id=sale_id)
        qr_screen.open()

class SplitPaymentModal(Popup):
    discount = NumericProperty(0)
    
    def __init__(self, total_due, customer_id, cart_items, callback, **kwargs):
        super().__init__(**kwargs)
        self.title = ''
        self.size_hint = (0.85, 0.6)
        self.original_total = total_due
        self.total_due = total_due
        self.customer_id = customer_id
        self.cart_items = cart_items
        self.callback = callback
        
        # build modal ui
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        with self.main_layout.canvas.before:
            Color(rgba=get_color_from_hex('#F2F2F7'))
            Rectangle(pos=self.main_layout.pos, size=self.main_layout.size)
        self.main_layout.bind(pos=lambda i,v: self._bg(i), size=lambda i,v: self._bg(i))
        
        self.header_lbl = Label(text=f"Total: Rs {total_due:,.2f}", bold=True, font_size=sp(22), color=get_color_from_hex('#1C1C1E'))
        self.main_layout.add_widget(self.header_lbl)
        
        disc = DiscountSelect()
        disc.controller = self 
        self.main_layout.add_widget(disc)
        
        btn = Button(text="Confirm Cash", size_hint_y=None, height=dp(50), background_color=get_color_from_hex('#34C759'))
        btn.bind(on_release=self.complete_sale)
        self.main_layout.add_widget(btn)
        
        self.content = self.main_layout

    def _bg(self, i):
        i.canvas.before.clear()
        with i.canvas.before:
            Color(rgba=get_color_from_hex('#FFFFFF'))
            RoundedRectangle(pos=i.pos, size=i.size, radius=[dp(16)])

    def set_discount(self, val):
        self.discount = val
        self.total_due = self.original_total * (1 - val)
        self.header_lbl.text = f"Total: Rs {self.total_due:,.2f} (-{int(val*100)}%)"

    def complete_sale(self, *args):
        try:
            conn = get_db_connection()
            c = conn.cursor()
            dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # create sale record
            c.execute("INSERT INTO sales (date, total, customer_id, qr_data) VALUES (%s,%s,%s,%s)", (dt, self.total_due, self.customer_id, "TEMP"))
            sale_id = c.lastrowid
            
            # generate bill url
            url = f"http://localhost:8000/bill/{sale_id}"
            c.execute("UPDATE sales SET qr_data=%s WHERE id=%s", (url, sale_id))
            
            # save items and update stock
            for item in self.cart_items:
                c.execute("INSERT INTO sales_items (sale_id, product_id, product_name, qty, price) VALUES (%s,%s,%s,%s,%s)",
                        (sale_id, item['id'], item['name'], int(item['qty']), item['price']))
                c.execute("UPDATE products SET stock = stock - %s WHERE id=%s", (int(item['qty']), item['id']))
                
            # record payment
            c.execute("INSERT INTO payments (sale_id, method, amount, timestamp) VALUES (%s,%s,%s,%s)", (sale_id, "cash", self.total_due, dt))
            conn.commit()
            conn.close()
            self.callback(sale_id)
            self.dismiss()
        except mysql.connector.Error as err:
            print(err)

class QRReceiptPopup(Popup):
    sale_id = NumericProperty(0)
    def __init__(self, sale_id, **kwargs):
        super().__init__(**kwargs)
        self.sale_id = sale_id
        self.title = ""
        self.separator_height = 0
        self.size_hint = (0.85, 0.75)
        
        # get qr url from db
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT qr_data, total FROM sales WHERE id=%s", (sale_id,))
        res = c.fetchone()
        qr_data = res[0]
        conn.close()
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        with layout.canvas.before:
            Color(rgba=get_color_from_hex('#FFFFFF'))
            RoundedRectangle(pos=layout.pos, size=layout.size, radius=[dp(20)])
        layout.bind(pos=lambda i,v: self._bg(i), size=lambda i,v: self._bg(i))
        
        layout.add_widget(Label(text="Success", font_size=sp(24), bold=True, color=get_color_from_hex('#1C1C1E'), size_hint_y=None, height=dp(40)))
        
        # generate qr image
        if HAS_QRCODE:
            qr = qrcode.QRCode(box_size=10)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            layout.add_widget(Image(texture=CoreImage(buf, ext='png').texture))
            
        layout.add_widget(Label(text="Scan for digital receipt", color=get_color_from_hex('#8E8E93'), size_hint_y=None, height=dp(30)))
        
        btn = Button(text="Done", size_hint_y=None, height=dp(50), background_color=get_color_from_hex('#007AFF'))
        btn.bind(on_release=self.dismiss)
        layout.add_widget(btn)
        
        self.content = layout

    def _bg(self, i):
        i.canvas.before.clear()
        with i.canvas.before:
            Color(rgba=get_color_from_hex('#FFFFFF'))
            RoundedRectangle(pos=i.pos, size=i.size, radius=[dp(20)])

class InventoryScreen(Screen):
    def upsert(self):
        n = self.ids.p_name.text.strip()
        cat = self.ids.p_cat.text
        if cat == "Select Category": return
        try: p = float(self.ids.p_price.text)
        except: p = 0
        try: s = int(self.ids.p_stock.text)
        except: s = 0
        if n and p > 0:
            try:
                conn = get_db_connection()
                c = conn.cursor()
                # insert new product
                c.execute("INSERT INTO products (name, category, price, stock) VALUES (%s,%s,%s,%s)", (n, cat, p, s))
                conn.commit()
                conn.close()
                self.ids.status.text = "Saved"
                self.ids.p_name.text = ""
            except mysql.connector.Error:
                self.ids.status.text = "DB Error"

class ReportScreen(Screen):
    def on_enter(self):
        self.generate_report()

    def generate_report(self):
        self.ids.report_area.clear_widgets()
        try:
            conn = get_db_connection()
            c = conn.cursor()
            # group payments by method
            c.execute("SELECT method, SUM(amount), COUNT(*) FROM payments GROUP BY method")
            group = ListGroup()
            self.ids.report_area.add_widget(group)
            for i, r in enumerate(c.fetchall()):
                row = ListRow()
                row.main_text = r[0].title()
                row.value_text = f"Rs {r[1]:,.0f}"
                row.is_last = False
                group.add_widget(row)
            conn.close()
        except mysql.connector.Error:
            pass

class DatabaseScreen(Screen):
    def on_enter(self):
        self.ids.search_box.text = ""
        self.show_products()

    def on_search(self, instance, value):
        self.show_products(value)

    def show_products(self, search=""):
        self.ids.db_list.clear_widgets()
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # build query with optional filter
            query = "SELECT name, category, price, stock FROM products"
            params = []
            if search:
                query += " WHERE name LIKE %s"
                params.append(f"%{search}%")
            query += " ORDER BY category ASC, name ASC"
            
            c.execute(query, tuple(params))
            rows = c.fetchall()
            conn.close()

            # group by category
            grouped_data = {}
            for row in rows:
                cat = row[1] if row[1] else "Uncategorized"
                if cat not in grouped_data:
                    grouped_data[cat] = []
                grouped_data[cat].append(row)

            if not grouped_data:
                lbl = Label(text="No products found", color=(0.5,0.5,0.5,1), size_hint_y=None, height=dp(50))
                self.ids.db_list.add_widget(lbl)
                return

            # render list
            for category, items in grouped_data.items():
                header = Label(
                    text=category.upper(),
                    color=get_color_from_hex('#8E8E93'),
                    bold=True,
                    font_size=sp(13),
                    size_hint_y=None,
                    height=dp(35),
                    halign='left',
                    valign='bottom',
                    text_size=(self.width, None)
                )
                header.bind(size=lambda instance, val: setattr(instance, 'text_size', (instance.width, None)))
                self.ids.db_list.add_widget(header)

                group = ListGroup()
                self.ids.db_list.add_widget(group)

                for i, r in enumerate(items):
                    row = ListRow()
                    row.main_text = r[0] 
                    row.sub_text = f"Rs {r[2]:,.2f}"
                    row.value_text = f"{r[3]} left"
                    # highlight low stock
                    if r[3] < 20:
                        row.value_text = f"[color=#FF3B30]{r[3]} left[/color]"
                        row.markup = True
                    if i == len(items) - 1:
                        row.is_last = True
                    group.add_widget(row)
        except mysql.connector.Error:
            pass

class CustomerScreen(Screen):
    def on_enter(self):
        self.show_customers()
    def add_customer(self):
        n = self.ids.c_name.text.strip()
        p = self.ids.c_phone.text.strip()
        e = self.ids.c_email.text.strip()
        if n:
            try:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("INSERT INTO customers (name, phone, email) VALUES (%s,%s,%s)", (n, p, e))
                conn.commit()
                conn.close()
                self.ids.status.text = "Saved"
            except mysql.connector.Error:
                self.ids.status.text = "DB Error"
    def show_customers(self):
        self.ids.cust_list.clear_widgets()
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT name, phone FROM customers ORDER BY name")
            group = ListGroup()
            self.ids.cust_list.add_widget(group)
            for r in c.fetchall():
                row = ListRow()
                row.main_text = r[0]
                row.value_text = r[1]
                row.is_last = False
                group.add_widget(row)
            conn.close()
        except mysql.connector.Error:
            pass

class SettingsScreen(Screen):
    def backup_db(self):
        self.ids.status_label.text = "Backup Done"
    def export_csv(self):
        self.ids.status_label.text = "Export Done"
    def show_about(self):
        popup = Popup(title="", size_hint=(0.7, 0.4), separator_height=0)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        with layout.canvas.before:
            Color(rgba=get_color_from_hex('#FFFFFF'))
            rect = RoundedRectangle(pos=(0,0), size=(100,100), radius=[dp(16)])
            
        def update_rect(instance, value):
            rect.pos = instance.pos
            rect.size = instance.size
        
        layout.bind(pos=update_rect, size=update_rect)
        
        layout.add_widget(Label(text="SwiftSale v2.2", font_size=sp(20), bold=True, color=get_color_from_hex('#1D1D1F')))
        layout.add_widget(Label(text="Enterprise Point of Sale", color=get_color_from_hex('#8E8E93'), halign='center'))
        btn = Button(text="Close", size_hint_y=None, height=dp(44), background_color=get_color_from_hex('#007AFF'))
        btn.bind(on_release=popup.dismiss)
        layout.add_widget(btn)
        popup.content = layout
        popup.open()

class SwiftApp(App):
    def build(self):
        init_db()
        Window.clearcolor = get_color_from_hex('#F4F7FE')
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(POSScreen(name='pos'))
        sm.add_widget(InventoryScreen(name='inventory'))
        sm.add_widget(ReportScreen(name='reports'))
        sm.add_widget(DatabaseScreen(name='database'))
        sm.add_widget(CustomerScreen(name='customers'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

if __name__ == '__main__':
    SwiftApp().run()