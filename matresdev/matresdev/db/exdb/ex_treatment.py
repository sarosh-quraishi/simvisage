#-------------------------------------------------------------------------------
#
# Copyright (c) 2009, IMB, RWTH Aachen.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in simvisage/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.simvisage.com/licenses/BSD.txt
#
# Thanks for using Simvisage open source!
#
# Created on Feb 15, 2010 by: rch

from etsproxy.traits.api import \
    HasTraits, Directory, List, Int, Float, Any, \
    on_trait_change, File, Constant, Instance, Trait, \
    Array, Str, Property, cached_property, WeakRef, \
    Dict, Button, Bool, Enum, Event

from etsproxy.util.home_directory import \
    get_home_directory

from etsproxy.traits.ui.api import \
    View, Item, DirectoryEditor, TabularEditor, HSplit, VGroup, \
    TableEditor, EnumEditor, Handler, FileEditor, VSplit, Group
    
from etsproxy.traits.ui.table_column import \
    ObjectColumn
    
from etsproxy.traits.ui.menu import \
    OKButton, CancelButton

from ex_run import ExRun

class ExTreatment( HasTraits ):
    
    runs = List( )
    
    #--------------------------------------------------------------------
    # file containing the association between the factor combinations 
    # and data files having the data 
    #--------------------------------------------------------------------
    data_file = File
    def _data_file_default(self):
        home_dir = os.environ['HOME']
        dat_dir = os.path.join( home_dir, 'workspace', 'simvisage', 'src', 'apps' )
        return dat_dir
    

    