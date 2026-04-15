from flask import Flask, render_template, request
import pyodbc

app = Flask(__name__)

# ডাটাবেস কানেকশন ফাংশন
def get_db_connection():
    server = '.\\SQLEXPRESS' 
    database = 'DreamTravels'
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    return pyodbc.connect(conn_str)

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
    # ডাটাবেস থেকে রুট অনুযায়ী বাস খোঁজা
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
    travel_date = request.form.get('travel_date')

    # সিট সংখ্যা গণনা করে মোট ভাড়া বের করা
    num_seats = len([s for s in seat_no.split(',') if s.strip()])

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # বাসের বিস্তারিত তথ্য আনা
    cursor.execute("SELECT BusName, RouteFrom, RouteTo, DepartureTime, ArrivalTime, Price FROM Buses WHERE BusID = ?", (bus_id,))
    bus_info = cursor.fetchone()

    if bus_info:
        single_price = float(bus_info[5])
        total_fare = single_price * num_seats 

        # --- নতুন অংশ: ডাটাবেসে বুকিং ডাটা সেভ করা ---
        try:
            insert_query = """
                INSERT INTO Bookings (PassengerName, BusID, SeatNumbers, TravelDate, TotalFare)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (passenger_name, bus_id, seat_no, travel_date, total_fare))
            conn.commit() # পরিবর্তনগুলো ডাটাবেসে সেভ করার জন্য এটি বাধ্যতামূলক
        except Exception as e:
            print("Database Error:", e)
        # -------------------------------------------

        conn.close()

        ticket_data = {
            'passenger': passenger_name,
            'bus_name': bus_info[0],
            'route': f"{bus_info[1]} to {bus_info[2]}",
            'seats': seat_no,
            'departure': str(bus_info[3])[:5], 
            'arrival': str(bus_info[4])[:5],
            'total_fare': "{:.2f}".format(total_fare),
            'date': travel_date if travel_date and travel_date != 'None' else "N/A"
        }
        return render_template('ticket.html', ticket=ticket_data)
    
    conn.close()
    return "Bus information not found", 404

if __name__ == '__main__':
    app.run(debug=True)