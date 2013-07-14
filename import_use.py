import sublime, sublime_plugin
import os, re

def get_use(class_name):
    return "use " + class_name + ";"

def get_class_fqn(namespace, class_name):
    return namespace.rstrip().replace("namespace ", "").replace(";", "")  + "\\" + class_name

class ImportUseCommand(sublime_plugin.TextCommand):
    namespaces = []

    def run(self, edit):
        s = None
        for region in self.view.sel():
            if not region.empty():
                s = self.view.substr(region)
                self.view.replace(edit, region, s)

        if not s:
            return

        window = self.view.window()
        baseFolder = window.folders()[0]
        vendorDirectory = baseFolder + "/vendor/"
        directoriesToExclude = set(['.git', 'tests', 'Tests', 'Test', 'test', 'docs', 'doc', 'documentation'])

        resultantFiles = set()
        for root, dirs, files in os.walk(vendorDirectory, topdown = True):
            files = [ f for f in files if not f[0] == '.' ]
            dirs[:] = [ d for d in dirs if not d in directoriesToExclude ]
            resultSet = set([(root + "/" + fname) for fname in files if fname.replace(".php", "") == s])
            resultantFiles = resultantFiles | resultSet

        for fileName in resultantFiles:
            pointer = open(fileName, "r")
            for line in pointer:
                if "namespace" in line:
                    self.namespaces.append(get_class_fqn(line, s));
                    pointer.close();
                    break
        if not self.namespaces:
            return

        window.show_quick_panel(self.namespaces, self.on_done)

    def on_done(self, selected_index):
        if selected_index == -1:
            self.namespaces = []
            return
        importedNamespace = self.namespaces[selected_index]
        
        self.view.run_command("add_use_to_file", { "namespace": importedNamespace })
        self.namespaces = []


class AddUseToFileCommand(sublime_plugin.TextCommand):
    def run(self, edit, namespace):
        region = self.view.find(re.escape(namespace), 0)
        if region:
            return sublime.status_message('The ' + namespace + ' namespace has already been imported!')

        regions = self.view.find_all(r"^\s*use\s[\w\\]+;", 0)

        if regions:
            last_region = regions[-1]
            line = self.view.line(last_region)
            contents = '\n' + get_use(namespace)
            self.view.insert(edit, line.end(), contents)
        else:
            region = self.view.find(r"^\s*namespace\s[\w\\]+;", 0)
            if region:
                line = self.view.line(region)
                contents = '\n\n' + get_use(namespace)
                self.view.insert(edit, line.end(), contents)
            else:
                return sublime.status_message('It seems the file is not namespaced... Are you using a >= PHP 5.3 project?')

        return True
