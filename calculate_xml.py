import xml.etree.ElementTree as ET
# tree = ET.parse('tripinfo.xml')
# root = tree.getroot()
# time = 0
# for vehicle in root.iter('tripinfo'):
#     #     print(vehicle.attrib['timeLoss'])
#     time += float(vehicle.attrib['timeLoss'])**2
# print('total timeLoss square for 30 run is ', time,
#       ', and average timeLoss square for 1 interval is ', time/30, '.')


def cal_average_time():
    import xml.etree.ElementTree as ET
    tree = ET.parse('tripinfo.xml')
    root = tree.getroot()
    time = 0
    num = 0
    for vehicle in root.iter('tripinfo'):
        #     print(vehicle.attrib['timeLoss'])
        time += float(vehicle.attrib['timeLoss'])**2
        num += 1
    print('total timeLoss square for 30 run is ', time, num,
          ', and average timeLoss square for 1 interval is ', time/num, '.')
    return time, num
