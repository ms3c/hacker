from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import sqlite3
import os
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = 'mamanet_secret_key_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'MamaNet_Advanced.sqlite')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_lookup_data():
    conn = get_db()
    genders = [r['Gender'] for r in conn.execute("SELECT Gender FROM GenderTypes").fetchall()]
    disabilities = [r['Disability'] for r in conn.execute("SELECT Disability FROM DisabilityTypes").fetchall()]
    payments = [r['Method'] for r in conn.execute("SELECT Method FROM PaymentMethods").fetchall()]
    conn.close()
    return genders, disabilities, payments

def build_filter_query(base_query, params):
    """Build filtered query based on request args"""
    conditions = []
    values = []
    
    age_group = params.get('age_group', '')
    district = params.get('district', '')
    payment = params.get('payment', '')
    
    if age_group:
        if age_group == 'under18':
            conditions.append("Age < 18")
        elif age_group == '18-35':
            conditions.append("Age BETWEEN 18 AND 35")
        elif age_group == '36-59':
            conditions.append("Age BETWEEN 36 AND 59")
        elif age_group == '60+':
            conditions.append("Age >= 60")
    
    if district:
        conditions.append("District = ?")
        values.append(district)
    
    if payment:
        conditions.append("PaymentMethod = ?")
        values.append(payment)
    
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    return base_query, values

@app.route('/')
def index():
    conn = get_db()
    
    # Get filter options
    districts = [r['District'] for r in conn.execute("SELECT DISTINCT District FROM Members WHERE District IS NOT NULL AND District != ''").fetchall()]
    _, _, payments = get_lookup_data()
    
    # Build filtered query
    query, values = build_filter_query("SELECT * FROM Members", request.args)
    query += " ORDER BY ID DESC"
    members = conn.execute(query, values).fetchall()
    conn.close()
    
    return render_template('index.html', members=members, districts=districts, payments=payments,
                          current_age=request.args.get('age_group', ''),
                          current_district=request.args.get('district', ''),
                          current_payment=request.args.get('payment', ''))

@app.route('/add', methods=['GET', 'POST'])
def add_member():
    genders, disabilities, payments = get_lookup_data()
    if request.method == 'POST':
        conn = get_db()
        conn.execute("""
            INSERT INTO Members (FullName, Age, PhoneNumber, Disability, OrganizationName, 
                                 PaymentMethod, ReceiverName, Gender, Address, Ward, District, Village)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['full_name'], request.form['age'], request.form['phone'],
            request.form['disability'], request.form['organization'], request.form['payment'],
            request.form['receiver'], request.form['gender'], request.form['address'],
            request.form['ward'], request.form['district'], request.form['village']
        ))
        conn.commit()
        conn.close()
        flash('Member added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('form.html', genders=genders, disabilities=disabilities, payments=payments, member=None)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_member(id):
    genders, disabilities, payments = get_lookup_data()
    conn = get_db()
    if request.method == 'POST':
        conn.execute("""
            UPDATE Members SET FullName=?, Age=?, PhoneNumber=?, Disability=?, OrganizationName=?,
                               PaymentMethod=?, ReceiverName=?, Gender=?, Address=?, Ward=?, District=?, Village=?
            WHERE ID=?
        """, (
            request.form['full_name'], request.form['age'], request.form['phone'],
            request.form['disability'], request.form['organization'], request.form['payment'],
            request.form['receiver'], request.form['gender'], request.form['address'],
            request.form['ward'], request.form['district'], request.form['village'], id
        ))
        conn.commit()
        conn.close()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('index'))
    member = conn.execute("SELECT * FROM Members WHERE ID=?", (id,)).fetchone()
    conn.close()
    return render_template('form.html', genders=genders, disabilities=disabilities, payments=payments, member=member)

@app.route('/delete/<int:id>')
def delete_member(id):
    conn = get_db()
    conn.execute("DELETE FROM Members WHERE ID=?", (id,))
    conn.commit()
    conn.close()
    flash('Member deleted successfully!', 'danger')
    return redirect(url_for('index'))

@app.route('/export')
def export_excel():
    conn = get_db()
    
    # Build filtered query (same filters as index)
    query, values = build_filter_query("SELECT * FROM Members", request.args)
    query += " ORDER BY ID"
    members = conn.execute(query, values).fetchall()
    conn.close()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Full Name', 'Age', 'Phone Number', 'Disability', 'Organization', 
                     'Payment Method', 'Receiver Name', 'Gender', 'Address', 'Ward', 'District', 'Village'])
    
    for m in members:
        writer.writerow([m['ID'], m['FullName'], m['Age'], m['PhoneNumber'], m['Disability'],
                        m['OrganizationName'], m['PaymentMethod'], m['ReceiverName'], m['Gender'],
                        m['Address'], m['Ward'], m['District'], m['Village']])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=members_export.csv'}
    )

@app.route('/reports')
def reports():
    conn = get_db()
    
    # Summary stats
    total = conn.execute("SELECT COUNT(*) FROM Members").fetchone()[0]
    
    # Gender distribution
    gender_data = conn.execute("""
        SELECT Gender, COUNT(*) as count FROM Members GROUP BY Gender
    """).fetchall()
    
    # Age group distribution
    age_data = conn.execute("""
        SELECT AgeGroup, COUNT(*) as count FROM AgeGroups GROUP BY AgeGroup
    """).fetchall()
    
    # Disability distribution
    disability_data = conn.execute("""
        SELECT Disability, COUNT(*) as count FROM Members GROUP BY Disability
    """).fetchall()
    
    # District distribution
    district_data = conn.execute("""
        SELECT District, COUNT(*) as count FROM Members WHERE District IS NOT NULL AND District != '' GROUP BY District
    """).fetchall()
    
    # Payment method distribution
    payment_data = conn.execute("""
        SELECT PaymentMethod, COUNT(*) as count FROM Members GROUP BY PaymentMethod
    """).fetchall()
    
    conn.close()
    
    return render_template('reports.html', 
                           total=total,
                           gender_data=gender_data,
                           age_data=age_data,
                           disability_data=disability_data,
                           district_data=district_data,
                           payment_data=payment_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

