import json
import sys
import io
import os
from flask import Flask, render_template, Blueprint, request

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Blueprint('fit_mafia', __name__, template_folder=template_dir)

@app.route('/test', methods=['GET'])
def test():
    return render_template('test.html')