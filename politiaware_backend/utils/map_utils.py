import json,os,django,sys
from typing import Literal


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'm.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def add_map(feature, obj):
    feature_properties = feature["properties"]
    geometry = GEOSGeometry(str(feature["geometry"]))  # accepts GeoJSON string
    # ensure geometry is MultiPolygon
    if geometry.geom_type == "Polygon":
        geometry = MultiPolygon(geometry)
    target_obj = obj[0] if isinstance(obj, (tuple, list)) else obj
    from state.models import State, StateMap
    from district.models import Districts, DistrictMap
    from taluk.models import Taluk, TalukMap

    if isinstance(target_obj, State):
        map_obj, _ = StateMap.objects.get_or_create(
            state=target_obj,
            defaults={"boundary": geometry, "feature_properties": feature_properties}
        )
        return map_obj
    elif isinstance(target_obj, Districts):
        map_obj, _ = DistrictMap.objects.get_or_create(
            district=target_obj,
            defaults={"boundary": geometry, "feature_properties": feature_properties}
        )
        return map_obj
    elif isinstance(target_obj, Taluk):
        map_obj, _ = TalukMap.objects.get_or_create(
            taluk=target_obj,
            defaults={"boundary": geometry, "feature_properties": feature_properties}
        )
        return map_obj


def add_map_loksabha(feature,dis_obj):
    geometry = GEOSGeometry(str(feature["geometry"]))  # accepts GeoJSON string
    # ensure geometry is MultiPolygon
    if geometry.geom_type == "Polygon":
        geometry = MultiPolygon(geometry)    
    from loksabha.models import LoksabhaConstituencyMap
    target_constituency = dis_obj[0] if isinstance(dis_obj, (tuple, list)) else dis_obj
    LoksabhaConstituency_obj = LoksabhaConstituencyMap.objects.get_or_create(
        loksabhaConstituency=target_constituency,
        defaults={"boundary": geometry}
    )

def load_map(type:Literal["state", "district", "taluk"],path):
    """
    To load both state and their map details. If state is unavailable, it will create and add map to it
    """
    
    #multiple_areas.objects.all().delete()
    data = read_json(path)
    features = data['features']
    if type == "state":
        from state.models import State
        #State.objects.all().delete()
        for feature in features :
            state_name = feature['properties']['NAME_1']
            if state_name == "Telangana" :
                status = "State"
            else :
                continue 
            status = feature['properties']['ENGTYPE_1']
            if status == "Union Territory":
                status = "UT" 
            state_obj = State.objects.get_or_create(
                Statename=state_name,
                Status=status
            )
            add_map(feature,state_obj)
    elif type == "district":
        from district.models import Districts
        from state.models import State
        Districts.objects.all().delete()
        for feature in features :
            state_obj = State.objects.filter(Statename=feature['properties']['NAME_1'])[0]
            if state_obj :
                dis_obj = Districts.objects.get_or_create(
                    state = state_obj,
                    districtName = feature['properties']['NAME_2']
                )
                add_map(feature,dis_obj)
            else :
                print("state name not found")
                
    elif type == "taluk":
        from taluk.models import Taluk   
    
def load_map_loksabha_const(path):
    """
    To load loksabha constituencies
    """
    missed_states = []
    data = read_json(path)
    features = data['features']
    from loksabha.models import LoksabhaConstituency
    from state.models import State
    from django.db.models import Q
    for feature in features:
        try:
            statename = feature['properties']['st_name']            
            state_obj = State.objects.filter(Q(Statename=statename) | Q(oldname=statename)).first()    
            if state_obj :
                dis_obj = LoksabhaConstituency.objects.get_or_create(
                    loksabhaConstituencyName = feature['properties']['pc_name']
                    ,state = state_obj
                )
                add_map_loksabha(feature,dis_obj)
                print(f"completed {statename}")
            else :
                print(f"state name not found - {statename}")
                missed_states.append(statename)
        except Exception as e:
            print(e)

    print(missed_states)



if __name__ == "__main__":
    #load_map(type="state",path="../../../maps_jsons/state/india_state.geojson")
    #load_map(type="state",path="../../../maps_jsons/state/india_telengana.geojson")
    #load_map(type="district",path="../../../maps_jsons/district/india_district.geojson")
    load_map_loksabha_const(path="../../../maps_jsons/loksabha/india_pc_2019_simplified.geojson")

    