import time
import psutil
import subprocess
import board
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import os
import socket

# Configuração do display OLED
WIDTH = 128
HEIGHT = 64

i2c = board.I2C()
oled_reset = digitalio.DigitalInOut(board.D4)
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, reset=oled_reset)

# Limpa o display
oled.fill(0)
oled.show()

# Criação de uma imagem para desenhar no display
image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

# Carregar a fonte FontAwesome para os ícones (certifique-se de que a fonte está no diretório correto)
icon_font = ImageFont.truetype("fa-solid-900.ttf", 12)  # Tamanho ajustável conforme necessidade
font = ImageFont.truetype("PixelOperator.ttf", 16)  # Fonte para o texto

# Códigos Unicode dos ícones FontAwesome
unicode_icons = {
    "processor": "\uf2db",  # CPU
    "thermometer": "\uf2c8",  # Temperatura
    "wifi": "\uf1eb",  # Wi-Fi/IP
    "tx": "\uf7c0",  # Transmitir
    "rx": "\uf519",  # Receber
    "microphone": "\uf130",  # Microfone
    "antenna": "\uf0c1"  # Antena
}

# Função para obter o IP local
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        ip = f"Erro IP: {e}"
    return ip

# Função para obter a temperatura da CPU
def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
        return f"{temp:.1f}°C"
    except FileNotFoundError:
        return "N/D"

# Função para exibir as informações na tela OLED
def update_oled(info_lines, tx_active, rx_active):
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
    
    # Exibir INTERLINK na parte amarela (fundo amarelo com texto preto)
    draw.rectangle((0, 0, oled.width, 15), fill=1)
    draw.text((oled.width // 2 - 30, 2), "INTERLINK", font=font, fill=0)
    
    # Exibir ícones e status
    draw.text((5, 20), unicode_icons["wifi"], font=icon_font, fill=255)  # Ícone de Wi-Fi
    draw.text((25, 20), info_lines['ip'], font=font, fill=255)  # IP
    
    draw.text((5, 35), unicode_icons["processor"], font=icon_font, fill=255)  # Ícone de CPU
    draw.text((25, 35), f"{info_lines['cpu']}%", font=font, fill=255)  # Uso de CPU
    
    draw.text((70, 35), unicode_icons["thermometer"], font=icon_font, fill=255)  # Ícone de temperatura
    draw.text((90, 35), info_lines['temp'], font=font, fill=255)  # Temperatura

    # Exibir status TX/RX em boxes lado a lado, presentes em ambas as telas
    if tx_active:
        draw.rectangle((5, 50, 60, 64), outline=1, fill=1)
        draw.text((15, 52), unicode_icons["tx"], font=icon_font, fill=0)  # Ícone TX
        draw.text((30, 52), "TX", font=font, fill=0)  # Texto TX
    else:
        draw.rectangle((5, 50, 60, 64), outline=1)
        draw.text((15, 52), unicode_icons["tx"], font=icon_font, fill=255)  # Ícone TX
        draw.text((30, 52), "TX", font=font, fill=255)  # Texto TX

    if rx_active:
        draw.rectangle((65, 50, 125, 64), outline=1, fill=1)
        draw.text((75, 52), unicode_icons["rx"], font=icon_font, fill=0)  # Ícone RX
        draw.text((90, 52), "RX", font=font, fill=0)  # Texto RX
    else:
        draw.rectangle((65, 50, 125, 64), outline=1)
        draw.text((75, 52), unicode_icons["rx"], font=icon_font, fill=255)  # Ícone RX
        draw.text((90, 52), "RX", font=font, fill=255)  # Texto RX

    # Atualiza o display OLED
    oled.image(image)
    oled.show()

# Função para monitorar o log do SVXLink e capturar a conferência e quem está falando
def monitor_svxlink_log():
    log_file = "/var/log/svxlink"
    if not os.path.exists(log_file):
        print("Log não encontrado")
        return "N/A", "LIVRE", "Livre para Recepcao"
    
    conference = "N/A"
    speaker = "LIVRE"
    current_status = "Livre para Recepcao"  # Status inicial
    
    try:
        with subprocess.Popen(['tail', '-n', '20', log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore') as log:
            for line in log.stdout:
                print(f"Log: {line.strip()}")
                
                # Conferência entre "from" e "---"
                if "EchoLink chat message received from" in line:
                    try:
                        # Extrai a conferência entre "from" e "---"
                        conference = line.split("from")[1].split("---")[0].strip()
                    except IndexError:
                        conference = "Erro na captura"
                
                # Quem está falando após "->"
                if "->" in line:
                    speaker = line.split("->")[1].strip()

                # Transmissão ativa ou livre para recepção
                if "Turning the transmitter ON" in line:
                    current_status = "Transmissao ativa"
                elif "Turning the transmitter OFF" in line:
                    current_status = "Livre para Recepcao"
                    
    except Exception as e:
        conference = "Erro Log"
        speaker = f"Erro Log: {e}"
    
    return conference, speaker, current_status

# Função principal
def main():
    screen_toggle = False  # Alterna entre tela 1 e tela 2
    try:
        while True:
            # Informações do sistema
            cpu = psutil.cpu_percent()
            temp = get_cpu_temperature()
            ip = get_ip_address()

            # Monitoramento do SVXLink para conferência e quem está falando
            conference, speaker, rx_tx_status = monitor_svxlink_log()

            # Alterna entre as telas a cada 5 segundos
            if screen_toggle:
                # Primeira tela: CPU, Temp, IP
                info_lines = {
                    "ip": ip,
                    "cpu": cpu,
                    "temp": temp
                }
                update_oled(info_lines, tx_active=(rx_tx_status == "Transmissao ativa"), rx_active=(rx_tx_status == "Livre para Recepcao"))
            else:
                # Segunda tela: Conferência e Quem está falando
                draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
                
                # Exibir INTERLINK na parte superior
                draw.rectangle((0, 0, oled.width, 15), fill=1)
                draw.text((oled.width // 2 - 30, 2), "INTERLINK", font=font, fill=0)

                # Exibir ícone de antena (conferência) e microfone (quem está falando)
                draw.text((5, 20), unicode_icons["antenna"], font=icon_font, fill=255)  # Ícone de antena
                draw.text((25, 20), conference, font=font, fill=255)

                draw.text((5, 35), unicode_icons["microphone"], font=icon_font, fill=255)  # Ícone de microfone
                draw.text((25, 35), speaker, font=font, fill=255)

                # Exibir status TX/RX em boxes lado a lado
                if rx_tx_status == "Transmissao ativa":
                    draw.rectangle((5, 50, 60, 64), outline=1, fill=1)
                    draw.text((15, 52), unicode_icons["tx"], font=icon_font, fill=0)  # Ícone TX
                    draw.text((30, 52), "TX", font=font, fill=0)  # Texto TX
                else:
                    draw.rectangle((5, 50, 60, 64), outline=1)
                    draw.text((15, 52), unicode_icons["tx"], font=icon_font, fill=255)  # Ícone TX
                    draw.text((30, 52), "TX", font=font, fill=255)  # Texto TX

                if rx_tx_status == "Livre para Recepcao":
                    draw.rectangle((65, 50, 125, 64), outline=1, fill=1)
                    draw.text((75, 52), unicode_icons["rx"], font=icon_font, fill=0)  # Ícone RX
                    draw.text((90, 52), "RX", font=font, fill=0)  # Texto RX
                else:
                    draw.rectangle((65, 50, 125, 64), outline=1)
                    draw.text((75, 52), unicode_icons["rx"], font=icon_font, fill=255)  # Ícone RX
                    draw.text((90, 52), "RX", font=font, fill=255)  # Texto RX

                # Atualiza o display OLED
                oled.image(image)
                oled.show()

            # Alterna a tela
            screen_toggle = not screen_toggle
            
            # Tempo de espera antes de alternar (ajustável)
            time.sleep(5)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
