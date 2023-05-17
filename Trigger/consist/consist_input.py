def get_layout_inputs(operatable_widget,activity_name,layout_file):
    widget_udid = str(operatable_widget.widget_udid)
    x1,y1,x2,y2 = operatable_widget.bounds
    coordinates = '['+str(int(x1))+','+str(int(y1))+']['+str(int(x2))+','+str(int(y2))+']'
    text_class = operatable_widget.text_class
    the_class = operatable_widget.operatable
    return widget_udid, coordinates, activity_name, text_class, the_class, layout_file
