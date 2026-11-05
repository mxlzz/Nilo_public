"""Nilo 0.5.9.3.4: expansión persistente y lectura de origen al seguir vínculos."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
HTML=(ROOT/'interfaz.html').read_text(encoding='utf-8')

class ExpansionAndNavigation(unittest.TestCase):
    def test_all_tabs_keep_expanded_details_across_rerender(self):
        self.assertIn('function feedExpandedDetails()',HTML)
        self.assertIn('function restoreFeedExpandedDetails(keys)',HTML)
        self.assertIn("renderedFeedTab===tab?feedExpandedDetails():new Set()",HTML)
        self.assertIn('restoreFeedExpandedDetails(expanded);',HTML)
        self.assertNotIn("tab==='activity'&&activityView==='featured'?[...el('feed').querySelectorAll",HTML)
        for attr in ('data-research-record','data-plan-id','data-measurement-record',
                     'data-proposal-id','data-agenda-record','data-entry-id'):
            self.assertIn("'"+attr+"'",HTML)

    @unittest.skipUnless(shutil.which('node'),'Node.js no disponible')
    def test_reexpanded_nested_record_not_dependent_on_list_position(self):
        js=HTML.split('<script>',1)[1].split('</script>',1)[0]
        start=js.index("const FEED_RECORD_ATTRIBUTES=")
        end=js.index("function drawFeed(){",start)
        helper=js[start:end]
        runner=r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const code=fs.readFileSync(process.argv[2],'utf8');
const feed={querySelectorAll(selector){return this.details.filter(node=>selector==='details'?true:node.open)},details:[]};
const context={tab:'research',el:id=>{assert.equal(id,'feed');return feed},Set};
vm.createContext(context);
vm.runInContext(code,context);
function detail(owner,n){
 const root={tagName:'DETAILS',open:n==='root',id:'',parentElement:{id:'feed'},
   hasAttribute:a=>a==='data-research-record',
   getAttribute:()=>owner,
   querySelectorAll:q=>q==='details'?this.children||[]:[],
   closest(){return this}};
 // Mock nested details by reference, with stable owner but moved list position
 const nested={tagName:'DETAILS',open:n==='nested',id:'',parentElement:root,
   closest(){return root},querySelectorAll(){return []}};
 root.querySelectorAll=()=>[nested];
 return {root,nested};
}
let before=detail('investigacion-123','nested');
before.root.open=true;before.nested.open=true;
feed.details=[before.root,before.nested];
const opened=vm.runInContext('feedExpandedDetails()',context);
assert.equal(opened.size,2);
let inserted=detail('investigacion-nueva','root');
inserted.root.open=false;inserted.nested.open=false;
let after=detail('investigacion-123','nested');
after.root.open=false;after.nested.open=false;
feed.details=[inserted.root,inserted.nested,after.root,after.nested];
context.saved=opened;
vm.runInContext('restoreFeedExpandedDetails(saved)',context);
assert.equal(after.root.open,true);
assert.equal(after.nested.open,true);
assert.equal(inserted.root.open,false);
assert.equal(inserted.nested.open,false);
"""
        with tempfile.TemporaryDirectory() as tmp:
            runner_path=Path(tmp)/'runner.js'
            code_path=Path(tmp)/'feed_functions.js'
            runner_path.write_text(runner)
            code_path.write_text(helper)
            p=subprocess.run(['node',str(runner_path),str(code_path)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)

    def test_following_related_or_measurement_link_marks_only_origin(self):
        self.assertIn('const origin=linkedReadOrigin(button);',HTML)
        self.assertIn('const origin=linkedReadOrigin(link);',HTML)
        self.assertEqual(HTML.count('finally{await markLinkedOriginRead(origin)}'),2)
        self.assertIn('async function markLinkedOriginRead(origin)',HTML)
        self.assertIn('await markRead(origin.category,origin.id,true)',HTML)
        self.assertIn('await markLocalEntryRead(origin.key,origin.tab)',HTML)
        self.assertIn("const entryTab=tab,id=card.dataset.entryId;",HTML)
        self.assertNotIn('markRead(button.dataset.relatedCategory',HTML)

if __name__=='__main__':
    unittest.main()
