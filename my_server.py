# First do:
#   python3 -m venv server_venv    
#   source server_venv/bin/activate
#   pip3 install flask

from flask import Flask, render_template 
app = Flask(__name__) 
app.config['DEBUG'] = True

@app.route('/') 
def home(): 
    return render_template('index.html') 

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/box')
def box():
    return render_template('box.html')

@app.route('/circle')
def circle():
    return render_template('bouncyball.html')

@app.errorhandler(404)
def not_found(e):
  return render_template('404_page.html'), 404

if __name__ == '__main__': 
    app.run(port=8000, debug=True)
