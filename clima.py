import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt

API_KEY = "0e05650e9ececb62f3cdc1d6cb842be4"
CITY = "Aguascalientes"
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=es"

class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clima - Qt5")
        self.setGeometry(200, 200, 300, 200)

        # Widgets
        self.city_label = QLabel(f"Ciudad: {CITY}", self)
        self.temp_label = QLabel("Temperatura: -- °C", self)
        self.desc_label = QLabel("Condición: --", self)

        self.city_label.setAlignment(Qt.AlignCenter)
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setAlignment(Qt.AlignCenter)

        self.update_button = QPushButton("Actualizar")
        self.update_button.clicked.connect(self.update_weather)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.city_label)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.desc_label)
        layout.addWidget(self.update_button)

        self.setLayout(layout)

    def update_weather(self):
        try:
            response = requests.get(URL)
            data = response.json()
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]

            self.temp_label.setText(f"Temperatura: {temp:.1f} °C")
            self.desc_label.setText(f"Condición: {desc.capitalize()}")
        except Exception as e:
            self.temp_label.setText("Error al obtener datos")
            self.desc_label.setText(str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec_())