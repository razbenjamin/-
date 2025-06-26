import csv
import os

from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'סופר-סוד-שלך'  # שים פה משהו אקראי ולא לפרסום
ADMIN_USER = 'admin'  # תחליף לשם שאתה רוצה שיהיה אדמין


# פונקציה לטעינת משתמשים מהקובץ
def load_users():
    users = {}
    with open('users.csv', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            users[row['username']] = row['password']
    return users

# דף התחברות
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="שם משתמש או סיסמה שגויים")

    return render_template('login.html')
@app.route('/delete-item', methods=['POST'])
def delete_item():
    if 'user' not in session or session['user'] != ADMIN_USER:
        return redirect(url_for('login'))

    product_to_delete = request.form['product']
    phone_to_delete = request.form['phone']
    new_rows = []

    with open('market.csv', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if not (row[1] == product_to_delete and row[4] == phone_to_delete):
                new_rows.append(row)

    with open('market.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(new_rows)

    return redirect(url_for('market'))

@app.route('/update-champion', methods=['POST'])
def update_champion():
    if 'user' not in session or session['user'] != ADMIN_USER:
        return redirect(url_for('login'))

    new_text = request.form['text']
    with open('champion.txt', 'w', encoding='utf-8') as file:
        file.write(new_text)

    image = request.files.get('image')
    if image and image.filename != '':
        image.save('static/champion.jpg')

    return redirect(url_for('champion'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']

    if request.method == 'POST':
        msg = request.form['message']
        with open('chat.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([username, msg])

        return redirect(url_for('chat'))

    messages = []
    try:
        with open('chat.csv', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                messages.append({'username': row[0], 'message': row[1]})
    except FileNotFoundError:
        pass

    return render_template('chat.html', messages=messages, username=username)
@app.route('/inbox')
def inbox():
    if 'user' not in session:
        return redirect(url_for('login'))

    current = session['user']
    users = []
    unread_users = set()

    for filename in os.listdir():
        if filename.startswith('chat_') and filename.endswith('.csv') and current in filename:
            # מחשבים מי המשתמש השני לפי שם הקובץ
            parts = filename.replace('chat_', '').replace('.csv', '').split('_')
            other_user = parts[0] if parts[1] == current else parts[1]

            if other_user != current:
                users.append(other_user)

            with open(filename, newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) == 3:
                        sender, _, status = row
                        if status == 'unread' and sender != current:
                            unread_users.add(sender)

    return render_template("inbox.html", users=users, unread_users=unread_users)

@app.route('/chat/<recipient>', methods=['GET', 'POST'])
def private_chat(recipient):
    if 'user' not in session:
        return redirect(url_for('login'))

    current = session['user']
    filename = f'chat_{min(current, recipient)}_{max(current, recipient)}.csv'

    # שליחה
    if request.method == 'POST':
        message = request.form['message']
        with open(filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([current, message, 'unread'])
        return redirect(url_for('private_chat', recipient=recipient))

    # ניקוי הודעות שלא נקראו
    temp_messages = []
    if os.path.exists(filename):
        with open(filename, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 3:
                    sender, msg, status = row
                    if sender == recipient and status == 'unread':
                        temp_messages.append([sender, msg, 'read'])
                    else:
                        temp_messages.append(row)
                else:
                    temp_messages.append(row)

        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(temp_messages)

    # הצגת שיחה
    messages = []
    if os.path.exists(filename):
        with open(filename, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    messages.append({'sender': row[0], 'message': row[1]})

    return render_template('private_chat.html', recipient=recipient, messages=messages, current=current)

    if os.path.exists(filename):
        with open(filename, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                messages.append({'sender': row[0], 'message': row[1]})

    return render_template('private_chat.html', messages=messages, recipient=recipient, current=current)

@app.route('/delete_item', methods=['POST'])
def delete_item_route():
    if 'user' not in session:
        return redirect(url_for('login'))

    to_delete = request.form['timestamp']
    current_user = session['user']
    updated_items = []

    with open('market.csv', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if not (row['timestamp'] == to_delete and row['username'] == current_user):
                updated_items.append(row)

    with open('market.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['username', 'title', 'desc', 'price', 'phone', 'timestamp'])
        writer.writeheader()
        writer.writerows(updated_items)

    return redirect(url_for('market'))


# דף הבית
@app.route('/home')
def home():
    if 'user' in session:
        return render_template('index.html', username=session['user'])
    else:
        return redirect(url_for('login'))

# דף אודות
@app.route('/champion', methods=['GET', 'POST'])
def champion():
    if 'user' not in session:
        return redirect(url_for('login'))

    # טקסט ברירת מחדל
    text = "אין עדיין מצטיין החודש."
    if os.path.exists('champion.txt'):
        with open('champion.txt', 'r', encoding='utf-8') as file:
            text = file.read()

    image_exists = os.path.exists('static/champion.jpg')
    is_admin = session['user'] == ADMIN_USER

    return render_template('champion.html', text=text, image_exists=image_exists, is_admin=is_admin)

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = session['user']
        product = request.form['product']
        price = request.form['price']
        description = request.form['description']
        phone = request.form['phone']

        # שמירה לקובץ
        with open('market.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([username, product, price, description, phone])

        return redirect(url_for('market'))

    return render_template('sell.html', username=session['user'])

@app.route('/market')
def market():
    if 'user' not in session:
        return redirect(url_for('login'))

    items = []
    try:
        with open('market.csv', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                items.append({
                    'username': row[0],
                    'product': row[1],
                    'price': row[2],
                    'description': row[3],
                    'phone': row[4]
                })
    except FileNotFoundError:
        pass

    return render_template('market.html', items=items)


# דף אירועים
@app.route('/calendar')
def calendar():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    events = []

    try:
        with open('events.csv', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username:
                    events.append({
                        'date': row[1],
                        'time': row[2],
                        'description': row[3]
                    })
    except FileNotFoundError:
        pass

    return render_template('calendar.html', username=username, events=events)

# דף פרופיל
@app.route('/profile')
def profile():
    if 'user' in session:
        return render_template('profile.html', username=session['user'])
    else:
        return redirect(url_for('login'))

# דף הגדרות
@app.route('/settings')
def settings():
    if 'user' in session:
        return render_template('settings.html', username=session['user'])
    else:
        return redirect(url_for('login'))

# התנתקות
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']

    if request.method == 'POST':
        current_pass = request.form['current']
        new_pass = request.form['new']

        users = load_users()

        if users[username] != current_pass:
            return render_template('change_password.html', error="סיסמה נוכחית שגויה")

        users[username] = new_pass
        with open('users.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'password'])
            for user, password in users.items():
                writer.writerow([user, password])

        return redirect(url_for('settings'))

    return render_template('change_password.html')

# הרצה
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
