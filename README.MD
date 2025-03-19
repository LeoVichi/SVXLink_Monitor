## INTERLINK OLED Monitor

Este projeto exibe informações do sistema e status do SVXLink em um display OLED SSD1306. Ele monitora a CPU, temperatura, IP e status de transmissão/recepção.

### Requisitos

- Raspberry Pi com interface I2C habilitada
- Display OLED SSD1306 (128x64)
- Python 3 instalado

### Instalação

Clone este repositório:
```sh
git clone https://github.com/seu-usuario/interlink-oled-monitor.git
cd interlink-oled-monitor
```

Instale as dependências:
```sh
pip install -r requirements.txt
```

### Uso

Execute o script principal:
```sh
python main.py
```

O display OLED alternará entre informações do sistema e status da transmissão do SVXLink a cada 5 segundos.

### Dependências
As bibliotecas necessárias estão listadas no arquivo `requirements.txt`. Caso precise instalar manualmente:
```sh
pip install psutil adafruit-circuitpython-ssd1306 pillow board digitalio
```

### Configuração do I2C no Raspberry Pi
Certifique-se de que o I2C está ativado:
```sh
sudo raspi-config
```
- Vá para *Interfacing Options* → *I2C* → *Enable*

Reinicie o sistema se necessário:
```sh
sudo reboot
```

### Autor
Desenvolvido por [Leonardo Vichi](https://github.com/seu-usuario).

