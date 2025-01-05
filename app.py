import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

package_tourism = pd.read_csv('database/package_tourism.csv')
tourism_rating = pd.read_csv('database/tourism_rating.csv')
tourism_with_id = pd.read_csv('database/tourism_with_id.csv')

def get_price_range(price):
    if price <= 50000:
        return "💰"
    elif price <= 100000:
        return "💰💰"
    else:
        return "💰💰💰"

def get_category_icon(category):
    icons = {
        'Alam': '🌲',
        'Budaya': '🏛️',
        'Buatan': '🎡',
        'Religi': '🕌',
        'Kuliner': '🍽️',
        'Sejarah': '🏺',
        'Belanja': '🛍️',
        'Pantai': '🏖️'
    }
    return icons.get(category, '🎯')

def get_recommendations(city=None, category=None, budget=None):
    df = tourism_with_id.copy()
    
    filters = []
    if city:
        filters.append(df['City'].str.lower() == city.lower())
    if category:
        filters.append(df['Category'].str.lower() == category.lower())
    if budget:
        filters.append(df['Price'] <= float(budget))
    
    if filters:
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        df = df[combined_filter]
    df = df.sort_values(['Rating', 'Price'], ascending=[False, True])
    
    return df[['Place_Name', 'Category', 'City', 'Price', 'Rating', 'Description']].head(10)

def get_package_recommendations(city):
    return package_tourism[package_tourism['City'].str.lower() == city.lower()].to_dict('records')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/assets/<filename>')
def serve_file(filename):
    return send_from_directory("assets", filename)

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.json['message'].lower()
    if user_message == 'menu':
        return jsonify({
            'response': """Silahkan pilih menu:<br>
1. Daftar Wisata<br>
2. Rekomendasi Wisata<br>
3. Paket Wisata""",
            'options': ['1', '2', '3']
        })
    elif user_message == '1':
        cities = tourism_with_id['City'].unique()
        return jsonify({
            'response': 'Pilih kota untuk melihat daftar wisata:',
            'options': cities.tolist()
        })
    
    elif user_message == '2':
        return jsonify({
            'response': """Pilih kriteria rekomendasi:<br>
1. Berdasarkan Kota<br>
2. Berdasarkan Kategori<br>
3. Berdasarkan Budget""",
            'options': ['1', '2', '3']
        })
    elif user_message == '2_2':
        categories = tourism_with_id['Category'].unique()
        return jsonify({
            'response': 'Pilih kategori wisata:',
            'options': categories.tolist()
        })
    elif user_message in tourism_with_id['Category'].str.lower().unique():
        recommendations = get_recommendations(category=user_message)
        response = f"Rekomendasi wisata kategori {user_message.title()}:<br><br>"
        
        for _, place in recommendations.iterrows():
            category_icon = get_category_icon(place['Category'])
            price_icon = get_price_range(place['Price'])
            
            response += f"{category_icon} <b>{place['Place_Name']}</b><br>"
            response += f"   Kategori: {place['Category']}<br>"
            response += f"   Kota: {place['City']}<br>"
            response += f"   Harga: {price_icon} Rp {place['Price']:,}<br>"
            response += f"   Rating: {'⭐' * int(round(place['Rating']))}<br>"
            if 'Description' in place and pd.notna(place['Description']):
                response += f"   Deskripsi: {place['Description']}<br>"
            response += "<br>"
            
        return jsonify({
            'response': response,
            'options': ['menu']
        })
    elif user_message == '2_3':
        budget_ranges = [
            "< Rp 50.000",
            "Rp 50.000 - Rp 100.000",
            "> Rp 100.000"
        ]
        return jsonify({
            'response': 'Pilih range budget:',
            'options': budget_ranges
        })
    elif user_message.startswith('budget_'):
        budget_range = user_message.split('_')[1]
        
        if budget_range == '1':
            max_budget = 50000
        elif budget_range == '2':
            max_budget = 100000
        else:
            max_budget = float('inf')
        
        recommendations = get_recommendations(budget=max_budget)
        
        if recommendations.empty:
            return jsonify({
                'response': "Maaf, tidak ditemukan wisata dengan kriteria tersebut.",
                'options': ['menu']
            })
        
        response = f"Rekomendasi wisata dengan budget {budget_range}:<br><br>"
        for _, place in recommendations.iterrows():
            category_icon = get_category_icon(place['Category'])
            price_icon = get_price_range(place['Price'])
            
            response += f"{category_icon} <b>{place['Place_Name']}</b><br>"
            response += f"   Kategori: {place['Category']}<br>"
            response += f"   Kota: {place['City']}<br>"
            response += f"   Harga: {price_icon} Rp {place['Price']:,}<br>"
            response += f"   Rating: {'⭐' * int(round(place['Rating']))}<br>"
            if 'Description' in place and pd.notna(place['Description']):
                response += f"   Deskripsi: {place['Description']}<br>"
            response += "<br>"
        
        return jsonify({
            'response': response,
            'options': ['menu']
        })
    
    elif user_message == '3':
        cities = package_tourism['City'].unique()
        return jsonify({
            'response': 'Pilih kota untuk melihat paket wisata:',
            'options': cities.tolist()
        })
    elif user_message in tourism_with_id['City'].str.lower().unique():
        places = tourism_with_id[tourism_with_id['City'].str.lower() == user_message]
        response = f"Daftar wisata di {user_message.title()}:<br><br>"
        
        for _, place in places.iterrows():
            category_icon = get_category_icon(place['Category'])
            price_icon = get_price_range(place['Price'])
            
            response += f"{category_icon} <b>{place['Place_Name']}</b><br>"
            response += f"   Kategori: {place['Category']}<br>"
            response += f"   Harga: {price_icon} Rp {place['Price']:,}<br>"
            response += f"   Rating: {'⭐' * int(round(place['Rating']))}<br>"
            if 'Description' in place and pd.notna(place['Description']):
                response += f"   Deskripsi: {place['Description']}<br>"
            response += "<br>"
        
        return jsonify({
            'response': response,
            'options': ['menu']
        })
    elif user_message.startswith('package_'):
        city = user_message.split('_')[1]
        packages = get_package_recommendations(city)
        
        if not packages:
            return jsonify({
                'response': f"Maaf, tidak ada paket wisata tersedia untuk kota {city.title()}.",
                'options': ['menu']
            })
        
        response = f"Paket Wisata di {city.title()}:<br><br>"
        for package in packages:
            response += f"🎫 <b>{package['Package']}</b><br>"
            response += f"   Harga: {'💰' * (package['Price'] // 500000 + 1)} Rp {package['Price']:,}<br>"
            response += f"   Durasi: ⏱️ {package['Duration']}<br>"
            if 'Included' in package and pd.notna(package['Included']):
                response += f"   Termasuk: ✅ {package['Included']}<br>"
            if 'Description' in package and pd.notna(package['Description']):
                response += f"   Deskripsi: {package['Description']}<br>"
            response += "<br>"
        
        return jsonify({
            'response': response,
            'options': ['menu']
        })
    return jsonify({
        'response': 'Maaf, saya tidak mengerti. Ketik "<b>menu</b>" untuk melihat pilihan menu.',
        'options': ['menu']
    })

if __name__ == '__main__':
    app.run(debug=True)