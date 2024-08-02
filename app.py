from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Настройка базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    apartment_number = db.Column(db.Integer, nullable=False)
    pet_name = db.Column(db.String(100), nullable=False)
    pet_breed = db.Column(db.String(100), nullable=False)
    walk_time = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'apartment_number': self.apartment_number,
            'pet_name': self.pet_name,
            'pet_breed': self.pet_breed,
            'walk_time': self.walk_time.strftime("%Y-%m-%dT%H:%M:%S")
        }


@app.route('/')
def home():
    return "Добро пожаловать в приложение для выгула собак!"


@app.route('/orders', methods=['GET'])
def get_orders():
    date_str = request.args.get('date')
    print(f"GET запрос с параметром даты: {date_str}")

    if not date_str:
        return jsonify({"error": "Нужно указать дату в формате YYYY-MM-DD"}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Неверный формат даты. Требуемый формат: YYYY-MM-DD"}), 400

    print(f"Распознанная дата: {date}")

    start_of_day = datetime(date.year, date.month, date.day)
    end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)

    orders = Order.query.filter(Order.walk_time >= start_of_day, Order.walk_time <= end_of_day).all()
    return jsonify([order.to_dict() for order in orders]), 200


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    print(f"POST запрос с данными: {data}")

    if not data:
        return jsonify({"error": "Тело запроса не должно быть пустым"}), 400

    required_fields = ['apartment_number', 'pet_name', 'pet_breed', 'walk_time']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Поле {field} обязательно"}), 400

    try:
        walk_time = datetime.strptime(data['walk_time'], '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        print(f"Полученное значение walk_time: {data.get('walk_time')}")
        print("Неверный формат времени, ожидалось: YYYY-MM-DDTHH:MM:SS")
        return jsonify({"error": "Неверный формат времени. Требуемый формат: YYYY-MM-DDTHH:MM:SS"}), 400

    print(f"Распознанное время прогулки: {walk_time}")

    # Проверка на время дня
    if not (7 <= walk_time.hour <= 23) or (walk_time.minute != 0 and walk_time.minute != 30):
        print(f"Недопустимый час или минуты: {walk_time.hour}:{walk_time.minute}")
        return jsonify(
            {"error": "Прогулка может начинаться либо в начале часа, либо в половину, между 7:00 и 23:00"}), 400

    existing_orders = Order.query.filter_by(walk_time=walk_time).count()
    if existing_orders >= 2:
        return jsonify({"error": "На это время уже записано 2 заказа"}), 400

    new_order = Order(
        apartment_number=data['apartment_number'],
        pet_name=data['pet_name'],
        pet_breed=data['pet_breed'],
        walk_time=walk_time
    )
    db.session.add(new_order)
    db.session.commit()

    return jsonify(new_order.to_dict()), 201


if __name__ == '__main__':
    app.run(debug=True)
