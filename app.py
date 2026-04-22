from flask import Flask, render_template, request
import pyodbc

app = Flask(__name__)

def get_db_connection():
    server = '.\\SQLEXPRESS' 
    database = 'DreamTravels'
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    return pyodbc.connect(conn_str)

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT B.BookingID, B.PassengerName, B.PassengerPhone, Bu.BusName, B.SeatNumbers, B.TotalFare, B.TravelDate 
        FROM Bookings B
        JOIN Buses Bu ON B.BusID = Bu.BusID
        ORDER BY B.BookingTime DESC
    """
    cursor.execute(query)
    bookings = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', bookings=bookings)
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['POST'])
def search_bus():
    from_loc = request.form.get('from-location')
    to_loc = request.form.get('to-location')
    travel_date = request.form.get('date')

    conn = get_db_connection()
    cursor = conn.cursor()
    # Findding buses from db by roots
    query = "SELECT * FROM Buses WHERE RouteFrom = ? AND RouteTo = ?"
    cursor.execute(query, (from_loc, to_loc))
    bus_list = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', buses=bus_list, from_loc=from_loc, to_loc=to_loc, date=travel_date)

@app.route('/book/<int:bus_id>')
def book_seat(bus_id):
    travel_date = request.args.get('date')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TotalSeats FROM Buses WHERE BusID = ?", (bus_id,))
    bus_data = cursor.fetchone()
    conn.close()

    total_seats = bus_data[0] if bus_data else 40 
    
    seats = []
    rows = "ABCDEFGHIJKL" 
    for i in range((total_seats // 4) + 1):
        for j in range(1, 5):
            if len(seats) < total_seats:
                seats.append(f"{rows[i]}{j}")
    
    return render_template('booking.html', bus_id=bus_id, seats=seats, travel_date=travel_date)

@app.route('/confirm', methods=['POST'])
def confirm_booking():
    bus_id = request.form.get('bus_id')
    seat_no = request.form.get('seat_no') 
    passenger_name = request.form.get('passenger_name')
    passenger_phone = request.form.get('passenger_phone') 
    travel_date = request.form.get('travel_date')

    num_seats = len([s for s in seat_no.split(',') if s.strip()])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Price FROM Buses WHERE BusID = ?", (bus_id,))
    bus_info = cursor.fetchone()
    total_fare = float(bus_info[0]) * num_seats if bus_info else 0
    conn.close()

    return render_template('payment.html', 
                           bus_id=bus_id, 
                           passenger_name=passenger_name,
                           passenger_phone=passenger_phone,
                           seat_no=seat_no,
                           travel_date=travel_date,
                           total_fare=total_fare)
@app.route('/process_payment', methods=['POST'])
def process_payment():
    bus_id = request.form.get('bus_id')
    seat_no = request.form.get('seat_no')
    passenger_name = request.form.get('passenger_name')
    passenger_phone = request.form.get('passenger_phone')
    travel_date = request.form.get('travel_date')
    total_fare = request.form.get('total_fare')
    payment_method = request.form.get('method')

    conn = get_db_connection()
    cursor = conn.cursor()
    insert_query = """
        INSERT INTO Bookings (PassengerName, PassengerPhone, BusID, SeatNumbers, TravelDate, TotalFare)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (passenger_name, passenger_phone, bus_id, seat_no, travel_date, total_fare))
    conn.commit()

    cursor.execute("SELECT BusName, DepartureTime, ArrivalTime FROM Buses WHERE BusID = ?", (bus_id,))
    bus_details = cursor.fetchone()
    conn.close()

    ticket_data = {
        'passenger': passenger_name,
        'seats': seat_no,
        'total_fare': total_fare,
        'date': travel_date,
        'method': payment_method,
        'bus_name': bus_details[0] if bus_details else "N/A",
        'departure': bus_details[1] if bus_details else "N/A",
        'arrival': bus_details[2] if bus_details else "N/A"
    }
    
    return render_template('ticket.html', ticket=ticket_data)

if __name__ == '__main__':
    app.run(debug=True)