import sys
from bs4 import BeautifulSoup
import requests
import time
import re
import csv
from urllib.parse import urljoin
from qtpy import QtWidgets
from PyQt5.QtCore import Qt

from ui.mainwindow import Ui_MainWindow

app = QtWidgets.QApplication(sys.argv)

url = "https://www.onvista.de"
company = ""

def get_search_results(url, company):
    namefound = 0
    while namefound == 0:
        pair = "suche/typ/aktien/" + company
        newurl = urljoin(url, pair)

        print(newurl)

        # get the url and parse it with BeautifulSoup
        r = requests.get(newurl)
        doc = BeautifulSoup(r.text, "html.parser")

        # Check if there exists a company with that name (if namefound == 0 then there is no company)
        a = ".SUCHE .AKTIE"
        getnum = []
        for i in doc.select(a):
            getnum.append(re.findall("[0-9]+", i.text))

        for i in getnum:
            if i != []:
                i[0] = int(i[0])
                if i[0] != 0:
                    namefound = 1

        # if you do not want to retry the search type in no (this will be changed to a retry button)
        # make an possible redo button in the widget
        if namefound == 0:
            redo = input("If you want to correct your input yes, else type no")
            if redo == "no":
                return
        else:
            return doc

# get the url and parse it with BeautifulSoup
def get_next_pages(url, next):
    return BeautifulSoup(requests.get(urljoin(url, next)).text, "html.parser")

def get_info(doc):
    info = []
    page = 1
    boolean = True
    if doc.select_one("div.BLAETTER_NAVI li a"):
        while boolean:
            number = doc.select("div.BLAETTER_NAVI li a")
            for i in number:
                if i.text != "weiter" and i.text != "zurück" and i.text != "erste Seite" and i.text != "letzte Seite":
                    if int(i.text) == (page + 1):
                        temppage = int(i.text)
                        boolean = False
                    elif int(i.text) == (page + 2):
                        boolean = True
            page = temppage
            for share in doc.select(".HERVORGEHOBEN .TEXT"):  # teste mit select_one
                gety = share.select("a")  # teste mit select_one
                inv_rel_check = share.select(".TEXT a.IR")
                if gety != None and gety != []:
                    # are there investor relations infos
                    for i in gety:
                        if inv_rel_check != []:
                            # if true then skip them
                            if i == inv_rel_check[0]:
                                continue
                            elif i.attrs["title"].lower().startswith(company):
                                infopart = []
                                infopart.append(i.attrs["href"])
                                infopart.append(i.attrs["title"])
                                infopart.append(i.text)
                                info.append(infopart)
                        elif i.attrs["title"].lower().startswith(company):
                            infopart = []
                            infopart.append(i.attrs["href"])
                            infopart.append(i.attrs["title"])
                            infopart.append(i.text)
                            info.append(infopart)
            if boolean == True:
                nextpage = "/suche/typ/aktien/" + company + "?assetType=Stock&blocksize=50&page=" + str(page)
                doc = get_next_pages(url, nextpage)
    else:
        for share in doc.select(".HERVORGEHOBEN"):  # teste mit select_one
            gety = share.select(".TEXT a")  # teste mit select_one
            inv_rel_check = share.select(".TEXT a.IR")
            if gety != None and gety != []:
                for i in gety:
                    # are there investor relations infos
                    if inv_rel_check != []:
                        # if true then skip them
                        if i == inv_rel_check[0]:
                            continue
                        elif i.attrs["title"].lower().startswith(company):
                            infopart = []
                            infopart.append(i.attrs["href"])
                            infopart.append(i.attrs["title"])
                            infopart.append(i.text)
                            info.append(infopart)
                    elif i.attrs["title"].lower().startswith(company):
                        infopart = []
                        infopart.append(i.attrs["href"])
                        infopart.append(i.attrs["title"])
                        infopart.append(i.text)
                        info.append(infopart)
    return info

def get_fundamentals_html(share_page, url):
    # get and parse the share's page
    r2 = requests.get(share_page)
    doc2 = BeautifulSoup(r2.text, "html.parser")

    # create, get and parse the fundamentals' page
    if doc2.select_one(".KENNZAHLEN a.WEITERFUEHRENDER_LINK"):
        get_fundamentals_url = doc2.select_one(".KENNZAHLEN a.WEITERFUEHRENDER_LINK").attrs["href"]
        r3 = requests.get(urljoin(url, get_fundamentals_url))
        doc3 = BeautifulSoup(r3.text, "html.parser")

        return doc3
    else:
        return "no fundamentals"

def get_numbers(doc3):
    numbers = []
    for num6 in doc3.select(".INHALT .KENNZAHLEN table tbody td.ZAHL"):
        a = num6.text.replace(".", "")
        a = a.replace(",", ".").split()
        if a == []:
            numbers.append("")
            #numbers.append(0)
        elif a == ["-"]:
            numbers.append("")
            #numbers.append(0)
        elif a[0].endswith("%"):
            a = a[0].replace("+", "")
            a = a.replace("%", "")
            a = float(a)
            a = a / 100
            numbers.append(round(a, 4))
        elif re.findall("[abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ]", a[0]):
            numbers.append(a[0])
        else:
            numbers.append(float(a[0]))

    return numbers

def sort_numbers(numbers, info, i):
    len_infotexts = 29
    row_length = int(int(len(numbers)) / len_infotexts)
    sorted_matrice = []

    print(info[i][1])
    l = info[i][1]
    sorted_matrice.append(l)
    for i in range(0, len_infotexts):
        for j in range(0, row_length):
            sorted_matrice.append(numbers[row_length * i + j])

    return sorted_matrice

def get_company_names():
    with open("company's names.csv", "r", newline='', encoding="utf-8") as csvfile:
        namereader = csv.reader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        company_names = [i for i in namereader]

        return company_names

#def choose_company(info):
#    c = input("Which company are you looking for?")
#    all_results = [i for i in info[1] if c in i]
#    return all_results

def csv_name_creator(info):
    with open("company's names.csv", "a", newline='', encoding="utf-8")as csvfile:
        namewriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for i in range(0, len(info)):
            namewriter.writerow([info[i][0], info[i][1], info[i][2]])

#company_names = get_company_names()
#list_of_companies = choose_company(info)
#print(list_of_companies)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None, list_of_companies=[], the_company=[], sorted_matrice=[], row=0):
        super().__init__(parent)
        self.list_of_companies = list_of_companies
        self.the_company = the_company
        self.sorted_matrice = sorted_matrice
        self.row = row

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.pushButton.clicked.connect(self.disp_input)
        self.ui.pushButton2.clicked.connect(self.clickedStock)

        self.ui.error_info.hide()
        self.ui.error_info_2.hide()
        self.ui.error_info_3.hide()

        self.ui.tableWidget.hide()
        self.ui.pushButton2.hide()

    def disp_input(self):
        company = self.ui.lineEdit.text()
        if company != "":
            if not self.ui.error_info.isHidden():
                self.ui.error_info.hide()
            with open("company's names.csv", "r", newline='', encoding="utf-8") as csvfile:
                namereader = csv.reader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                company_names = []
                for i in namereader:
                    company_names.append(i)

            self.list_of_companies = [i for i in company_names if company.lower() in i[1].lower()]

            self.ui.tableWidget.show()
            self.ui.pushButton2.show()
            self.ui.pushButton.hide()
            self.newRow(self.list_of_companies)
            return self.list_of_companies
        else:
            self.ui.error_info.show()

    #def keyPressEvent(self, event):
     #   if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
      #      self.disp_input

    def clickedStock(self, list_of_companies):
        if self.ui.tableWidget.currentItem() == None:
            self.ui.error_info_2.show()
            return
        else:
            if not self.ui.error_info_2.isHidden():
                self.ui.error_info_2.hide()
            self.row = self.ui.tableWidget.currentItem().row()

            while self.ui.tableWidget.rowCount() > 0:
                self.ui.tableWidget.removeRow(0)
            self.ui.tableWidget.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Indicators"))
            self.the_company = self.list_of_companies[self.row]
            self.getSortedMatrice(url)
            return

    def newRow(self, company_list):
        if len(company_list) == 0:
            rows = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(rows)
            self.ui.tableWidget.setItem(rows, 0, QtWidgets.QTableWidgetItem(company_list[1]))
        else:
            for i in range(0, len(company_list)):
                rows = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.insertRow(rows)
                self.ui.tableWidget.setItem(rows, 0, QtWidgets.QTableWidgetItem(company_list[i][1]))
        return

    def sortNumbers(self, numbers):
        # row_length = int(len(numbers) / len(infotexts))
        len_infotexts = 29
        row_length = int(int(len(numbers)) / len_infotexts)
        self.sorted_matrice = []

        print(self.the_company[1])
        l = self.the_company[1]
        self.sorted_matrice.append(l)
        for i in range(0, len_infotexts):
            for j in range(0, row_length):
                self.sorted_matrice.append(numbers[row_length * i + j])
        return self.sorted_matrice

    def getSortedMatrice(self, url):
        sharepage = urljoin(url, self.the_company[0])
        print(sharepage)

        if sharepage:
            doc3 = get_fundamentals_html(sharepage, url)
            if doc3 != "no fundamentals":
                numbers = get_numbers(doc3)
                self.sorted_matrice = self.sortNumbers(numbers)
                # len(sorted_matrice) = 204
            else:
                self.ui.tableWidget.error_info_4.show()
        else:
            self.ui.tableWidget.error_info_3.show()

    def setIndicators(self):
        print("Got here")
        pass

window = MainWindow()
window.show()

sys.exit(app.exec_())
