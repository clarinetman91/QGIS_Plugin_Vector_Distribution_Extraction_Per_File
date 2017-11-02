# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VectorDistributionExtractionPerFile
                                 A QGIS plugin
 This extract the distribution of one vector layer in each feature of a second vector layer
                              -------------------
        begin                : 2017-03-05
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Kevin Bourrand
        email                : k.bourrand@hotmail.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QAbstractItemView, QTableWidgetItem, QLineEdit
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from vector_distribution_extraction_per_file_dialog import VectorDistributionExtractionPerFileDialog
import os.path
import processing
from qgis.core import *
from PyQt4.QtCore import QVariant, Qt, QObject
from PyQt4 import QtGui
from PyQt4.QtGui import QFont, QBrush, QColor
from qgis.gui import QgsMessageBar
import time

class VectorDistributionExtractionPerFile:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'VectorDistributionExtractionPerFile_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Vector Distribution Extraction Per File')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'VectorDistributionExtractionPerFile')
        self.toolbar.setObjectName(u'VectorDistributionExtractionPerFile')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('VectorDistributionExtractionPerFile', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/VectorDistributionExtractionPerFile/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Write the distribution of one or several vector layers/files in each feature of an area vector layer/file'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Vector Distribution Extraction Per File'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def highlight_doubles(self):
        """This function highlight the headers of each row that are doubled in the selected distribution layers/files table.
        In orange if the doubled headers are both from the added fields, in yellow if an added field doubles a field from the original area table"""
        # Instantiate a list that will contain all the headers name of the currently selected area vector file/layer 
        area_headers_list = []
        # Test if there's at least one area vector file/layer currently selected
        if len(area_lyr_list) > 0:
            # Test if the "with only id and new fields" check box is unticked
            if self.dlg.checkBox_4.isChecked() == False:
                # Populate area_headers_list with the preexisting field names in the currently selected area vector file/layer, from this point, all the field names are converted to lower case
                for field in area_lyr_list[self.dlg.comboBox.currentIndex()].pendingFields():
                    area_headers_list.append(field.name().lower())
            # Add the name of the currently selected id field 
            else:
                area_headers_list.append(self.dlg.comboBox_2.currentText().lower())
        # Instantiate a set that will contain all the headers that will be added to the output. As a set this won't contain doubled members
        added_headers_set = set()
        # Instantiate two lists that will contain all the headers that will be painted in yellow and in orange
        yellow_list = []
        orange_list = []
        # Iterate through the lines of the tableWidget that sum-up all the selected distribution vector file/layer 
        for row_number in range(0, self.dlg.tableWidget.rowCount()):
            # Instantiate the current header as a string 
            current_row_header = self.dlg.tableWidget.cellWidget(row_number,1).text()
            # Append the current header to the yellow_list if it is present in the area_headers_list already
            if current_row_header.lower() in area_headers_list:
                yellow_list.append(current_row_header.lower())
            # Append the current header to the orange_list if it is present in the added_headers_set already
            if current_row_header.lower() in added_headers_set:
                orange_list.append(current_row_header.lower())
            # Add the current header to the added_headers_set
            added_headers_set.add(current_row_header.lower())    
        # Iterate through the lines of the tableWidget a second time
        for row_number in range(0, self.dlg.tableWidget.rowCount()):
            # Instantiate the current header widget
            current_header_widget = self.dlg.tableWidget.cellWidget(row_number,1)
            # Change the colour of the widget in yellow if its text value is present in the yellow_list
            if current_header_widget.text().lower() in yellow_list:
                current_header_widget.setStyleSheet("background-color: yellow")
            # Change the colour of the widget in orange if its text value is present in the orange_list    
            if current_header_widget.text().lower() in orange_list:
                current_header_widget.setStyleSheet("background-color: orange")
            # Change the colour of the widget in white if its text value is neither present in the orange_list nor the yellow list
            if current_header_widget.text().lower() not in yellow_list and current_header_widget.text().lower() not in orange_list:
                current_header_widget.setStyleSheet("background-color: white")
    
    def highlight_unmatching_crs(self):
        """This function highlight the crs of each row that is not the same as the input area vector file/layer in the selected distribution layers/files table"""
        # Check if the area_lyr_list (this list is containing every instantiated layer item that are currently shown in the "Select areas vector file/layer" combo box) is containing at least one item
        if len(area_lyr_list) > 0: 
            # Instantiate a set that will contain all the layers/files having a different crs as the input area vector file/layer crs
            mismatching_lyr_set = set()
            # Instantiate the current area vector file/layer crs description
            area_crs = area_lyr_list[self.dlg.comboBox.currentIndex()].crs().description()
            # Instantiate an iterator that will increment following the index of the current row 
            row_number = 0
            # Iterate through the table_lyr_list (this list is containing every instantiated layer item that are currently shown on the "select distribution vector files/layers" table)
            for layer in table_lyr_list:
                # Change the colour of the widget containing the crs information to red if it's different from the area_crs
                if layer[0].crs().description() != area_crs:
                    self.dlg.tableWidget.item(row_number,3).setBackground(QBrush(QColor("red")))
                    # Add the current layer/file name to the mismatching_lyr_set
                    mismatching_lyr_set.add(table_lyr_list[row_number][0].name())
                # Otherwise, change it to white
                else:
                    self.dlg.tableWidget.item(row_number,3).setBackground(QBrush(QColor("white")))
                # Increment the row_number by one
                row_number += 1
            # Show a message bar including a list of the crs mismatching layers/files if there's any
            if len(mismatching_lyr_set)>0:
                self.iface.messageBar().pushMessage("Warning", "Some of the distribution layer's CRS () are mismatching the CRS of the area layer: %s" % mismatching_lyr_set, level=QgsMessageBar.WARNING,duration=5)

    def area_vector_path(self):
        """This function loads a path for an area vector file that is not instantiated on the canvas as a layer"""
        # Instantiate an empty string as the default_input_path
        default_input_path = ""
        # Replace the empty string by the path stored the key 'Processing/LastInputPath' if it exists 
        if 'Processing/LastInputPath' in QSettings().allKeys():
            default_input_path = QSettings().value('Processing/LastInputPath')
        # Open a dialogue box in the default_input_path to allow the selection of the desired area vector path
        file_name = QFileDialog.getOpenFileName(self.dlg, "Select Input Area Vector File",default_input_path, '*.shp') # getOpenFileName method allow only one entry
        # Add the selected area vector path to the combo box and to the area_lyr_list if the dialogue doesn't return an empty string
        if file_name != "":
            area_lyr_list.append(QgsVectorLayer(file_name, "%s" %(os.path.basename(file_name)), "ogr"))
            self.dlg.comboBox.addItem(file_name)
            # Set the current combo box index to the selected area vector file
            self.dlg.comboBox.setCurrentIndex(self.dlg.comboBox.count()-1)
            # Set the 'Processing/LastInputPath' to the selected area vector path 
            QSettings().setValue('Processing/LastInputPath',os.path.dirname(file_name))
        
    def shift_selected_layer_to_the_right(self):
        """This function shifts the selected distribution layers to the "selected distribution vector files/layers" table (on the right) with their covering values"""
        # Instantiate a list of the selected item found in the "select distribution vector files/layers" (on the left)
        selected_item = self.dlg.listWidget.selectedItems()
        # Instantiate a QBrush object with the colour grey that will serves to change the coulour of the text of some of the item that will be added to the table
        grey_brush = QBrush(QColor(80, 80, 80,255))
        # Fill the "selected distribution vector files/layers" with the items in "select distribution vector files/layers" giving the "Absolute surfaces" covering value if the corresponding check box is ticked
        if self.dlg.checkBox_1.isChecked():
            # Instantiate an iterator that will increment following the value of the current index
            current_list_index = 0
            # Iterate through the selected_item list
            for item in selected_item:
                # Instantiate the numbre of rows contained in the "selected distribution vector files/layers" table
                row_count = self.dlg.tableWidget.rowCount()
                # Add a new row to the table
                self.dlg.tableWidget.setRowCount(row_count + 1)
                # Instantiate an editable QLineEdit object containing the current item text with a limitation of 10 characters (this will be the output header name)
                C1 = QLineEdit(item.text()[:10])
                C1.setMaxLength(10)
                # Place the QLineEdit object in the last row of the table at the 2nd column
                self.dlg.tableWidget.setCellWidget(row_count,1,C1)
                # Instantiate a non editable QTableWidgetItem object containing the current item text (this will display the name of the intersected distribution layer/file)
                C0 = QTableWidgetItem(item.text())
                C0.setFlags(Qt.ItemIsEditable)
                # Set the characters colour of the item to grey
                C0.setForeground(grey_brush)
                # Place the QTableWidgetItem object in the last row of the table at the 1st column
                self.dlg.tableWidget.setItem(row_count,0,C0)
                # Instantiate an non editable QTableWidgetItem object containing the text 'absolute' (this will display the type of covering value attached to the distribution layer/file)
                C2 = QTableWidgetItem('absolute')
                C2.setFlags(Qt.ItemIsEditable)
                C2.setForeground(grey_brush)
                # Place the QTableWidgetItem object in the last row of the table at the 3rd column
                self.dlg.tableWidget.setItem(row_count,2,C2)
                # Instantiate a non editable QTableWidgetItem object containing the crs of the current item (this will display the type of covering value attached to the distribution layer/file)
                C3 = QTableWidgetItem(left_lyr_list[self.dlg.listWidget.selectedIndexes()[current_list_index].row()].crs().description())
                C3.setFlags(Qt.ItemIsEditable)
                C3.setForeground(grey_brush)
                # Place the QTableWidgetItem object in the last row of the table at the 4th column
                self.dlg.tableWidget.setItem(row_count,3,C3)
                # Append the a two members item containing to the table_lyr_list:[0] the layer [1] the covering type
                table_lyr_list.append([left_lyr_list[self.dlg.listWidget.row(item)],'Absolute surfaces'])
                # Connect all the edits made on the editable field (C1) to the function 'highlight_doubles' 
                self.dlg.tableWidget.cellWidget(row_count,1).textChanged.connect(self.highlight_doubles)
                # Increment the current index
                current_list_index += 1
                
        # Same as above with the "Ratio" covering value if the corresponding check box is ticked
        if self.dlg.checkBox_2.isChecked():
            current_list_index = 0
            for item in selected_item:
                row_count = self.dlg.tableWidget.rowCount()
                self.dlg.tableWidget.setRowCount(row_count + 1)
                C1 = QLineEdit(item.text()[:10])
                C1.setMaxLength(10)
                self.dlg.tableWidget.setCellWidget(row_count,1,C1)
                C0 = QTableWidgetItem(item.text())
                C0.setFlags(Qt.ItemIsEditable)
                C0.setForeground(grey_brush)
                self.dlg.tableWidget.setItem(row_count,0,C0)
                C2 = QTableWidgetItem('ratio')
                C2.setFlags(Qt.ItemIsEditable)
                C2.setForeground(grey_brush)
                self.dlg.tableWidget.setItem(row_count,2,C2)
                C3 = QTableWidgetItem(left_lyr_list[self.dlg.listWidget.selectedIndexes()[current_list_index].row()].crs().description())
                C3.setFlags(Qt.ItemIsEditable)
                C3.setForeground(grey_brush)
                self.dlg.tableWidget.setItem(row_count,3,C3)
                table_lyr_list.append([left_lyr_list[self.dlg.listWidget.row(item)],'Ratio']) 
                self.dlg.tableWidget.cellWidget(row_count,1).textChanged.connect(self.highlight_doubles)
                current_list_index += 1
    
    def load_distribution_vector(self):
        """This function loads path for distribution vector files that are not instantiated on the canvas as a layer"""
        # Instantiate an empty string as the default_input_path
        default_input_path = ""
        # Replace the empty string by the path stored the key 'Processing/LastInputPath' if it exists 
        if 'Processing/LastInputPath' in QSettings().allKeys():
            default_input_path = QSettings().value('Processing/LastInputPath')
        # Open a dialogue box in the default_input_path to allow the selection of the single or multiple areas vector path
        file_name_list = QFileDialog.getOpenFileNames(self.dlg, "Select Input Distribution Vector File",default_input_path, '*.shp') # getOpenFileNames method allow multiple entries
        # Instantiate a list that will contain the filenames to be added to the "Select distribution vector files/layers" table
        filtered_layer_list = []
        # Instantiate a list that will contain the filenames that has been refused because of the geometry type 
        refused_file_name_list = []
        # Iterate through the file_name_list
        for file_name in file_name_list:
            # Instantiate the current file_name as a QgsVectorLayer
            layer = QgsVectorLayer(file_name, "%s"% os.path.basename(file_name), "ogr")
            # Add the layer to the filtered_layer_list if it's geometry is made of polygons
            if layer.geometryType() == QGis.Polygon: 
                filtered_layer_list.append(layer)
            # Otherwise, add it to the refused_file_name_list
            else:
                refused_file_name_list.append(layer.source())
        # Iterate through the filtered_layer_list
        for layer in filtered_layer_list:
            # Add the current layer to the widget and to the left_lyr_list
            self.dlg.listWidget.addItem(layer.name())
            # Set the current row to the last item (this also select all the input files/layers)
            self.dlg.listWidget.setCurrentRow(self.dlg.listWidget.count()-1)
            # Append the current layer to the left_lyr_list
            left_lyr_list.append(layer)
        # Set the 'Processing/LastInputPath' to the directory name of the first member of the filtered_layer_list if the list contains at least 1 item that is not en empty string
        if len(filtered_layer_list)>0:
            if filtered_layer_list[0] != "":
                QSettings().setValue('Processing/LastInputPath',os.path.dirname(file_name))
        # Show a message bar containing the name of the refused files if refused_file_name_list contains at least one member
        if len(refused_file_name_list)>0:
            self.iface.messageBar().pushMessage("Warning", "The following shapefiles weren't polygon and therefore hadn't been added: %s" % refused_file_name_list, level=QgsMessageBar.WARNING)

    def remove_line(self):
        """This function removes the selected lines from the "selected distribution vector files/layers" """
        # Instantiate a list that will contain all the row indexes to be deleted from the table
        row_list = []
        # Store the indexes of the selected rows of the tableWidget in the row_list
        for index in self.dlg.tableWidget.selectedIndexes():
            row_list.append(index.row())
        # Invert the order of the indexes in the list and loop on it to delete the selected rows from the table
        for reversed_index in row_list[::-1]: 
            self.dlg.tableWidget.removeRow(reversed_index)
            del table_lyr_list[reversed_index]
    
    def make_editable(self):
        """This function enables/disables a bunch of widgets depending whether the "create new table" check box is being ticked or not"""
        if self.dlg.checkBox_3.isChecked() == False:
            self.dlg.checkBox_4.setEnabled(False)
            self.dlg.lineEdit.setEnabled(False)
            self.dlg.pushButton_3.setEnabled(False)
            self.dlg.comboBox_2.setEnabled(False)
            self.dlg.label_4.setEnabled(False)
            self.dlg.label_2.setEnabled(False)
            
        if self.dlg.checkBox_3.isChecked() == True:
            self.dlg.checkBox_4.setEnabled(True)
            self.dlg.lineEdit.setEnabled(True)
            self.dlg.pushButton_3.setEnabled(True)
            self.dlg.label_4.setEnabled(True)
            if self.dlg.checkBox_4.isChecked() == True:
                self.dlg.comboBox_2.setEnabled(True)
                self.dlg.label_2.setEnabled(True)
            
    
    def make_limited_field_editable(self):
        """This function enables/disables a bunch of widgets depending whether the "with only id and new fields" option is being ticked or not"""
        if self.dlg.checkBox_4.isChecked() == False:
            self.dlg.comboBox_2.setEnabled(False)
            self.dlg.label_2.setEnabled(False)
        if self.dlg.checkBox_4.isChecked() == True:
            self.dlg.comboBox_2.setEnabled(True)
            self.dlg.label_2.setEnabled(True)
        
    def load_output_path(self):
        """This function loads an output path"""
        # Instantiate an empty string as the default_output_path
        default_output_path = ""
        # Replace the empty string by the path stored the key 'Processing/LastInputPath' if it exists 
        if 'Processing/LastOutputPath' in QSettings().allKeys():
            default_output_path = QSettings().value('Processing/LastOutputPath')
        # Open a dialogue box in the default_output_path to allow the selection of the output path
        file_name = QFileDialog.getSaveFileName(self.dlg, "Select Output Table",default_output_path, '*.shp')
        # Write the file_name if it's not an empty string to the lineEdit object 
        if file_name != "":
            self.dlg.lineEdit.setText(file_name)
            # Set the 'Processing/LastOutputPath' to the selected output path 
            QSettings().setValue('Processing/LastOutputPath',os.path.dirname(file_name))
            
        
    def load_id_field(self):
        """This function fill up the id field combo box with the fields of the currently selected area vector file/layer"""
        # Erase the items from the comboBox object
        self.dlg.comboBox_2.clear()
        # Fill up the comboBox object with the fields of the currently selected area vector file/layer
        for field in area_lyr_list[self.dlg.comboBox.currentIndex()].pendingFields():
            self.dlg.comboBox_2.addItem(field.name())
    
    def display_area_crs(self):
        """This function displays the crs of the currently selected area vector file/layer into the textBrowser_2 object"""
        if self.dlg.comboBox.count() > 0:
            self.dlg.textBrowser_2.setText(area_lyr_list[self.dlg.comboBox.currentIndex()].crs().description())
        
    def run(self):
        """This function prepares the dialogue before opening it"""
        global left_lyr_list, table_lyr_list, area_lyr_list
        # Create the dialog (after translation) and keep reference
        self.dlg = VectorDistributionExtractionPerFileDialog()
        # Add the correct number of column in the table
        self.dlg.tableWidget.setRowCount(0)
        self.dlg.tableWidget.setColumnCount(4)
        # Add the headers in the "selected distribution vector files/layers" table
        HEADERS = ['vector layer or file','header name','absolute/ratio','CRS (Unmatching crs in red)']
        self.dlg.tableWidget.setHorizontalHeaderLabels(HEADERS)
        # Set the column width to the headers
        self.dlg.tableWidget.resizeColumnsToContents()
        # Instantiate the height of the table and instantiate the width of the table as 0
        total_height = self.dlg.tableWidget.height()
        total_width = 0
        # Iterate on the the columns of the "selected distribution vector files/layers" table to get the total width of the table
        for colrank in range(0,len(HEADERS)):
            total_width = total_width + self.dlg.tableWidget.columnWidth(colrank)
        # Resize the tableWidget to the added width of it's columns plus 23 pixels
        self.dlg.tableWidget.resize(total_width + 23,total_height)
        # Establish connections between interface clicked signals and functions
        self.dlg.pushButton.clicked.connect(self.area_vector_path)
        self.dlg.pushButton_4.clicked.connect(self.load_distribution_vector)
        self.dlg.pushButton_2.clicked.connect(self.shift_selected_layer_to_the_right)
        self.dlg.pushButton_2.clicked.connect(self.highlight_doubles)
        self.dlg.pushButton_2.clicked.connect(self.highlight_unmatching_crs)
        self.dlg.pushButton_5.clicked.connect(self.remove_line)
        self.dlg.pushButton_5.clicked.connect(self.highlight_doubles)
        self.dlg.pushButton_5.clicked.connect(self.highlight_unmatching_crs)
        self.dlg.checkBox_3.clicked.connect(self.make_editable)
        self.dlg.checkBox_4.clicked.connect(self.make_limited_field_editable)
        self.dlg.checkBox_4.clicked.connect(self.highlight_doubles)
        self.dlg.pushButton_3.clicked.connect(self.load_output_path)
        self.dlg.pushButton_6.clicked.connect(self.process)
        self.dlg.pushButton_7.clicked.connect(self.dlg.close)
        # Instantiate three lists that will contain the layer instantiated items equivalent of the different tables 
        left_lyr_list = []
        table_lyr_list = []
        area_lyr_list = []
        # Fill up the left list widget and the comboBox with all the vector layer in the workspace append the layer instantiated item equivalents at the same time
        layer_list = self.iface.legendInterface().layers()
        for layer in layer_list:
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Polygon: 
                self.dlg.listWidget.addItem(layer.name())
                left_lyr_list.append(layer)
                self.dlg.comboBox.addItem(layer.name())
                area_lyr_list.append(layer)
        # Establish connections between the signals of an index change in the combo boxes and some functions
        self.dlg.comboBox.currentIndexChanged.connect(self.highlight_doubles)
        self.dlg.comboBox.currentIndexChanged.connect(self.highlight_unmatching_crs)
        self.dlg.comboBox.currentIndexChanged.connect(self.load_id_field)
        self.dlg.comboBox.currentIndexChanged.connect(self.display_area_crs)
        self.dlg.comboBox_2.currentIndexChanged.connect(self.highlight_doubles)
        # Allow the multiple selections in the list widget
        self.dlg.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        # Set the first tab to be displayed first
        self.dlg.tabWidget.setCurrentIndex(0)
        # Call the load_id_function if there's at least one area vector layer loaded in the area_lyr_list
        if len(area_lyr_list)> 0:
            self.load_id_field()
        # Call several function to fill up specific widgets before showing the dialogue
        self.make_editable()
        self.make_limited_field_editable()
        self.display_area_crs()
        # Show the dialogue
        self.dlg.show()
        
    def process(self):
        # Raise an error message bar if the area vector file/layer combo box does not have any item in it
        if self.dlg.comboBox.count() == 0:
            self.iface.messageBar().pushMessage("Warning", "No area vector file/layer has been selected", level=QgsMessageBar.CRITICAL,duration=5)
        # Raise an error message bar if the "selected distribution vector file/layer" table does not have any item in it
        elif self.dlg.tableWidget.rowCount() == 0:
            self.iface.messageBar().pushMessage("Warning", "No distribution vector file/layer has been selected", level=QgsMessageBar.CRITICAL,duration=5)
        # Raise an error message bar if the "load the output vector file path"  lineedit is empty as the checkbox_4 is ticked
        elif self.dlg.checkBox_3.isChecked() == True and self.dlg.lineEdit.text() == "":
            self.iface.messageBar().pushMessage("Warning", "No output vector file path has been selected as the 'create a new table' has been ticked", level=QgsMessageBar.CRITICAL,duration=5)
        # Otherwise, perform the rest of the process
        else:
            # Disable the main tab
            self.dlg.tab.setEnabled(False)
            # Display a message in the status text browser
            self.dlg.textBrowser.setText("Initialization")
            # Add the header name as the third member of each list representing the processed layers in table_lyr_list
            iter = 0
            for layer in table_lyr_list:
                table_lyr_list[iter].append(self.dlg.tableWidget.cellWidget(iter,1).text())
                iter += 1
            # Get the input vector area from the dialog, filled up by the user
            lyr_vector_area = area_lyr_list[self.dlg.comboBox.currentIndex()]
            # If both checkboxes (3 and 4) are ticked, write a copy of the input area layer at the place filled up by the user in the lineEdit object with only the one field selected in the comboBox_2
            if self.dlg.checkBox_3.isChecked() == True:
                if self.dlg.checkBox_4.isChecked() == True:
                    # Instantiate a new empty QgsFields object
                    fields = QgsFields()
                    # Add the field selected in the comboBox_2
                    fields.append(QgsField(self.dlg.comboBox_2.currentText(), lyr_vector_area.fields()[self.dlg.comboBox_2.currentIndex()].type()))
                    # Set a writer object that will write the features of the input area vector layer into the new file
                    writer = QgsVectorFileWriter(self.dlg.lineEdit.text(), lyr_vector_area.dataProvider().encoding(), fields, lyr_vector_area.wkbType(), lyr_vector_area.crs(), "ESRI Shapefile")
                    # Add the features of lyr_vector_area to the new file
                    for feature in lyr_vector_area.getFeatures():
                        new_feature = QgsFeature()
                        new_feature.setGeometry(feature.geometry())
                        new_feature.setAttributes([feature[self.dlg.comboBox_2.currentText()]])
                        writer.addFeature(new_feature)
                    # Delete the writer to flush features to disk
                    del writer
                    # Instantiate the newly created vector file as a qgsvectorlayer and add it to the map canvas
                    lyr_vector_area = self.iface.addVectorLayer(self.dlg.lineEdit.text(), "%s"% os.path.basename(self.dlg.lineEdit.text()), "ogr")
                else:
                    # If only checkbox 3 is ticked, write a copy of the input area layer at the place filled up by the user in the lineEdit object
                    QgsVectorFileWriter.writeAsVectorFormat(lyr_vector_area,self.dlg.lineEdit.text(),lyr_vector_area.dataProvider().encoding(),lyr_vector_area.crs(),"ESRI Shapefile")
                    # Instantiate the newly created vector file as a qgsvectorlayer and add it to the map canvas
                    lyr_vector_area = self.iface.addVectorLayer(self.dlg.lineEdit.text(), "%s"% os.path.basename(self.dlg.lineEdit.text()), "ogr")

            # Iterate through the area layer to get to store the surface of all the objects in a dictionnary
            iter = lyr_vector_area.getFeatures()
            surf_dict = {}
            counter = 0
            for feature in iter:
                geom = feature.geometry()
                area = geom.area()
                surf_dict[feature.id()]= area
                counter += 1
            # Get the number of column from lyr_vector_area
            input_area_col_count = 0
            for field in lyr_vector_area.pendingFields():
                input_area_col_count += 1
            # Create a temporary Id column to be used as reference to the areas feature after the intersection
            lyr_vector_area.dataProvider().addAttributes([QgsField("id_temp", QVariant.Int)])
            # Fill the column with the id's
            for feature in lyr_vector_area.getFeatures():
                lyr_vector_area.dataProvider().changeAttributeValues({ feature.id() : {input_area_col_count: feature.id()}})
            lyr_vector_area.updateFields()
            # Refresh the canvas so that the intersection processing will take account of the previous modifications in case the involved layers are open on the canvas
            self.iface.mapCanvas().refreshAllLayers()
            # Instantiate the index of the column containing the temporary id's
            id_col = input_area_col_count 
            # Instantiate the index of the column that will contain the result of the first intersection (this will increment with the new added columns)
            result_col = input_area_col_count + 1
            # Instantiate an empty dictionnary that will contain all the distribution layers sources as the keys with their temporary outputs layers (coming from the intersection processing) as the value
            output_lyr_dict = {}
            lyr_counter = 1
            for distribution_layer in table_lyr_list:
                # Display a message showing the currently processed layer
                self.dlg.textBrowser.setText("(%s/%s) The layer '%s' is being processed with the covering value '%s'" % (lyr_counter,len(table_lyr_list),distribution_layer[0].name(),distribution_layer[1]))
                # If the source of the currently processed layer is present in the dictionnary, Instantiate its value as a layer 
                if distribution_layer[0].source() in output_lyr_dict:
                    lyr_vector_ouput = output_lyr_dict[distribution_layer[0].source()]
                # Otherwise run the intersection
                else:
                    # Run the intersection geoprocessing and store the path to vector_output as a new dictionary
                    vector_output = processing.runalg("qgis:intersection",lyr_vector_area,distribution_layer[0],None)
                    # Get the value of the dictionary given by the key 'OUTPUT'
                    lyr_vector_ouput = QgsVectorLayer(vector_output['OUTPUT'], "vector output", "ogr")
                    # Delete all the features that aren't including geometry
                    iter = lyr_vector_ouput.getFeatures()
                    for feature in iter:
                        if feature.geometry() == None:
                            lyr_vector_ouput.dataProvider().deleteFeatures([feature.id()])
                    output_lyr_dict[distribution_layer[0].source()] = lyr_vector_ouput 

                # Add one field that will contain the distribution of the current distribution_layer, its name will be the truncated name of the source of the current distribution_layer
                lyr_vector_area.dataProvider().addAttributes([QgsField("%s"% (distribution_layer[2]), QVariant.Double)])
                # Fill it with 0's               
                iter = lyr_vector_area.getFeatures()
                for feature in iter:
                    lyr_vector_area.dataProvider().changeAttributeValues({ feature.id() : {result_col:0}})
                # Iterate through the attribute of the result table of the intersection
                iter = lyr_vector_ouput.getFeatures() 
                for feature in iter:
                    if feature[id_col] != NULL:# maybe, break the loop when arriving in the end of the area feature since these are coming first in the intersection output
                        # Set a request to get the feature from the area layer indicated in the temporary id_col in the output of the intersection
                        request = QgsFeatureRequest().setFilterFid(feature[id_col])
                        area_feat = lyr_vector_area.getFeatures(request).next()
                        # Calculate the area of the current feature
                        geom = feature.geometry()
                        featurearea = geom.area()
                        # Calculate the relative area of the feature regarding the surface of the original feature in the area layer
                        relarea = featurearea/surf_dict[feature[id_col]]
                        # Add the relative area if the corresponding check box has been ticked
                        if distribution_layer[1] == "Ratio":
                            lyr_vector_area.dataProvider().changeAttributeValues({ feature[id_col] : {result_col:relarea + area_feat[result_col]}})
                        # Add the absolute surface if the corresponding check box has been ticked
                        if distribution_layer[1] == "Absolute surfaces":
                            lyr_vector_area.dataProvider().changeAttributeValues({ feature[id_col] : {result_col:featurearea + area_feat[result_col]}})
                               
                # Increment the column reference by one
                result_col += 1
                # Update the fields and refresh the canvas 
                lyr_vector_area.updateFields()
                self.iface.mapCanvas().refreshAllLayers()
                # Increment the lyr_counter
                lyr_counter += 1
            # Delete the temporary id field
            lyr_vector_area.dataProvider().deleteAttributes([id_col])
            # Update the fields and refresh the canvas
            lyr_vector_area.updateFields()
            self.iface.mapCanvas().refreshAllLayers()
            # Close the dialogue
            self.dlg.close()
            del lyr_vector_area
            del lyr_vector_ouput 