import logging
import sys
from collections import defaultdict

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                             QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QMenu, QMessageBox, QPushButton,
                             QTableWidget, QTableWidgetItem, QToolButton,
                             QWidget, QLayout)

import RiotAPI
from utils import KDA

class KDATable(QDialog):
    def __init__(self, parent, kda_data):
        logger.info('Initializing pop-up')
        super(KDATable, self).__init__(parent)
        self.setGeometry(300, 300, 600, 1000)
        self.kda_data = kda_data
        self.initUI()
        logger.info('Done initializing pop-up')

    def initUI(self):
        self.setWindowTitle('Big Inters Player Analysis')
        player_table = QTableWidget(len(self.kda_data), 5, self)
        player_table.setHorizontalHeaderLabels(['Summoner', 'Occurences', 'Kills', 'Deaths', 'Assists'])
        for r, (summoner, data) in enumerate(self.kda_data.items()):
            player_table.setItem(r, 0, QTableWidgetItem(str(summoner)))
            player_table.setItem(r, 1, QTableWidgetItem(str(data[0])))
            player_table.setItem(r, 2, QTableWidgetItem(str(data[1].kills)))
            player_table.setItem(r, 3, QTableWidgetItem(str(data[1].deaths)))
            player_table.setItem(r, 4, QTableWidgetItem(str(data[1].assists)))

        layout = QGridLayout()
        layout.addWidget(player_table, 0, 0)
        self.setLayout(layout)


class Application(QWidget):
    def __init__(self):
        logger.info('Initializing main window')
        super().__init__()
        self.RAR = RiotAPI.RiotApiRequester(RiotAPI.API_KEY, 'NA1')
        self.initUI()
        logger.info('Initialization done')

    def initUI(self):
        self.setWindowTitle('Big Inters')
        self.setGeometry(200, 200, 400, 150)

        self.summoner_box = QLineEdit(self)
        self.summoner_box.setPlaceholderText('Summoner Name')

        self.region_sel = QComboBox(self)
        self.region_sel.addItems(['NA1', 'EUW1'])
        self.region_sel.currentTextChanged.connect(
            lambda reg: setattr(self.RAR, 'region', reg))
        region_sel_layout = QHBoxLayout()
        region_sel_layout.addWidget(QLabel('Region:', self))
        region_sel_layout.addWidget(self.region_sel)

        self.matches_box = QLineEdit(self)
        self.matches_box.setPlaceholderText('Number of Matches')
        match_validator = QtGui.QIntValidator()
        match_validator.setRange(1, 90)
        self.matches_box.setValidator(match_validator)

        queue_button = QToolButton(self)
        queue_button.setText('Select Queue Types')
        self.queue_menu = QMenu(self)
        for q in RiotAPI.QUEUE_TYPES.keys():
            action = self.queue_menu.addAction(q)
            action.setCheckable(True)
        queue_button.setMenu(self.queue_menu)
        queue_button.setPopupMode(QToolButton.InstantPopup)

        self.run_btn = QPushButton('Run', self)
        self.run_btn.clicked.connect(self.run_analysis)

        self.quit_btn = QPushButton('Quit', self)
        self.quit_btn.clicked.connect(QApplication.instance().quit)

        layout = QGridLayout()
        layout.addWidget(self.summoner_box, 0, 0)
        layout.addLayout(region_sel_layout, 0, 1)
        layout.addWidget(self.matches_box, 1, 0)
        layout.addWidget(queue_button, 1, 1)
        layout.addWidget(self.run_btn, 2, 0)
        layout.addWidget(self.quit_btn, 2, 1)
        self.setLayout(layout)

        self.analysis_window = None

    def run_analysis(self):
        logger.info('Starting player analysis')
        summoner = self.summoner_box.text()
        matches = self.matches_box.text()
        queues = []
        for action in self.queue_menu.actions():
            if action.isChecked():
                queues.append(RiotAPI.QUEUE_TYPES[action.text()])

        if matches == '':
            matches = '10'

        summoner_r = self.RAR.get(
            f'/lol/summoner/v4/summoners/by-name/{summoner}')
        account_eid = summoner_r.json()['accountId']

        matches_r = self.RAR.get(
            f'/lol/match/v4/matchlists/by-account/{account_eid}', endIndex=[matches], queue=queues)
        matches = matches_r.json()['matches']

        player_kdas = defaultdict(lambda: [0, KDA()])

        for match in matches:
            match_r = self.RAR.get(f'/lol/match/v4/matches/{match["gameId"]}')

            players = match_r.json()['participantIdentities']
            players = dict([(player['participantId'], player['player']
                             ['summonerName']) for player in players])

            player_data = match_r.json()['participants']

            for player in player_data:
                summoner_name = players[player['participantId']]
                player_kdas[summoner_name][0] += 1
                for val in ('kills', 'deaths', 'assists'):
                    player_kda = player_kdas[summoner_name][1]
                    setattr(player_kda, val, getattr(
                        player_kda, val) + player['stats'][val])

        player_kdas = {k: v for k, v in sorted(
            player_kdas.items(), key=lambda KDA: KDA[1][0], reverse=True)}

        self.analysis_window = KDATable(self, player_kdas)
        self.analysis_window.show()
        logger.info('Analysis finished')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s')

    logger = logging.getLogger('app')

    app = QApplication(sys.argv)
    main = Application()
    main.show()
    sys.exit(app.exec_())
