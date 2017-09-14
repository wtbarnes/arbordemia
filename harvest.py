#Will Barnes
#3 April 2016
#harvest.py

import logging
import wikipedia
import re
from graphviz import Digraph
from bs4 import BeautifulSoup

class TreeClimber(object):
    """Traverse wiki tree, grabbing parents and children"""

    def __init__(self,seed,sibling_depth=100):
        """Constructor for TreeClimber class"""
        self.logger = logging.getLogger(type(self).__name__)
        try:
            wikipedia.page(seed)
            self.seed = seed
        except wikipedia.PageError:
            self.logger.exception('Cannot find Wikipedia page for %s. Try another starting point.'%seed)

        self.tree = Digraph('G')


    def _search_info_table(self,wpage,tval):
        """Search the Wikipedia info table for tval"""

        if type(tval) is not list:
            tval = [tval]

        table = wpage.find('table',{'class':'infobox vcard'})
        if table is None:
            self.logger.warning('No table found. Returning None.')
            return None

        res = None
        for tr in table.find_all('tr'):
            if tr.find('th') is None:
                continue
            for tv in tval:
                if tr.find('th').get_text().lower() == tv.lower():
                    res = tr.find('td').get_text()
                    break

        return res

    def _none_filter(self,res):
        """Return empty string if None"""
        if res is None:
            return ''
        return str(res)

    def _res_filter(self,res):
        """Filter out junk that may stop search"""
        if res is None:
            return None
        ref = re.compile('\[\d\]')
        find_junk = ref.findall(res)
        for f in find_junk:
            res = res.replace(f,'')

        return res


    def climb_tree(self):
        """Climb the tree"""

        branch_found = True
        cur_branch = self.seed
        prev_node = None
        while cur_branch is not None:
            self.logger.debug('Current branch is %s'%cur_branch)
            #Get wikipedia page
            try:
                cur_page = wikipedia.page(cur_branch)
            except wikipedia.PageError:
                self.logger.exception('Cannot find page for %s. Ending search.'%cur_branch)
                self.tree.node(cur_branch)
                self.tree.edge(cur_branch,prev_node)
                cur_branch = None
                continue
            except wikipedia.DisambiguationError:
                self.logger.exception('Multiple pages found for query %s. Adding "(physicist)" and searching again.')
                cur_page = wikipedia.page(cur_branch+' (physicist)')

            #parse the table
            html_source = BeautifulSoup(cur_page.html(),'html.parser')
            advisor = self._search_info_table(html_source,['Doctoral advisor','Doctoral advisors','Academic advisors','Academic advisor'])
            alma_mater = self._search_info_table(html_source,'Alma mater')
            students = self._search_info_table(html_source,'Doctoral students')
            #add to graph
            self.tree.node(cur_branch,cur_branch+'\n'+self._none_filter(alma_mater))
            if prev_node is not None:
                self.tree.edge(cur_branch,prev_node)
            #update
            prev_node = cur_branch
            cur_branch = self._res_filter(advisor)


    def show_tree(self):
        self.tree.view()
