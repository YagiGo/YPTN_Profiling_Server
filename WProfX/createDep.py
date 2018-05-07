import json
from bokeh.plotting import figure
from bokeh.models import Range1d
class DrawRelationMap():
    def __init__(self, inputFile, outputFile):
        self.jsonFile = inputFile #  input the file here
        with open(self.jsonFile) as dataFile:
            self.data = json.load(dataFile)
        self.endTime = int(self.data[-1]['networkingTime']) + int(self.data[-1]['computationTime'])
        self.yRange = len(self.data) + 10
        self.lineWidth = 4
        # self.yr = Range1d(start=self.yRange, end=0)
        # self.xr = Range1d(start=0, end= 1.05*self.endTime)
        self.p = figure(plot_width=1250, plot_height=2100, tools=['save,pan,wheel_zoom,reset,resize'], x_axis_location="above")
        ################################################################################################################
        # Basic Plot Setting
        ################################################################################################################
        self.p.xaxis.axis_label = 'Time (ms)'
        self.p.xaxis.axis_label_text_align = 'left'
        self.p.xaxis.axis_label_text_color = "#c8c8c8"
        self.p.xaxis.axis_label_text_font_size = '10pt'
        self.p.xaxis.axis_line_color = '#c8c8c8'
        self.p.xaxis.major_tick_line_color = '#c8c8c8'
        self.p.xaxis.major_label_text_color = '#c8c8c8'
        self.p.xaxis.major_label_text_align = 'left'
        self.p.xaxis.major_label_text_font_size = '10pt'
        self.p.xaxis.minor_tick_line_color = '#c8c8c8'
        self.p.xaxis.minor_tick_out = 0
        self.p.xgrid.grid_line_alpha = 0.5
        self.p.ygrid.grid_line_color = None
        self.p.yaxis.visible = False
        self.javascript_type_list = ['application/x-javascript', 'application/javascript', 'application/ecmascript',
                                     'text/javascript', 'text/ecmascript', 'application/json', 'javascript/text']
        self.css_type_list = ['text/css', 'css/text']
        self.text_type_list = ['evalhtml', 'text/html', 'text/plain', 'text/xml']
        self.colormap = dict(ctext='#2757ae', dtext="#a8c5f7", cjs="#c9780e", djs='#e8ae61', ccss="#13bd0d",
                             dcss='#8ae887',
                             cother="#eb5bc0", dother='#eb5bc0', img='#c79efa')

    def drawAllDependencies(self):
        for dep in self.data[-1]['objs']:
            a1_id = dep['a1']
            a2_id = dep['a2']

    def testInput(self):
        for index, event in enumerate(self.data):
            try:
                print(event['id'])
            except Exception:
                pass





if __name__ == "__main__":
    testObj = DrawRelationMap("./graphs/0_www.yahoo.co.jp.json", './testoutptu.html')
    testObj.testInput()
    testObj.drawAllDependencies()