# -*- coding: utf-8 -*-
import sys
import os
import traceback
import json
import time
import java.lang.Throwable
from java.lang import Class
from java.io import FileInputStream, File
from org.openstreetmap.josm.spi.preferences import Config, MemoryPreferences, IBaseDirectories

WORK_DIR = os.environ.get("QABOT_WORK_DIR", "/data/work")

class HeadlessDirs(IBaseDirectories):
    def getPreferencesDirectory(self, create): return File(WORK_DIR)
    def getUserDataDirectory(self, create): return File(WORK_DIR)
    def getCacheDirectory(self, create): return File(WORK_DIR)

Config.setBaseDirectoriesProvider(HeadlessDirs())
pref = MemoryPreferences()
Config.setPreferencesInstance(pref)

from org.openstreetmap.josm.data.projection import Projections, ProjectionRegistry
proj = Projections.getProjectionByCode("EPSG:3857")
ProjectionRegistry.setProjection(proj)
print("Projection set: " + str(ProjectionRegistry.getProjection().toString()))
sys.stdout.flush()

pref.putBoolean("validator.CrossingWays.test_buildings", True)
pref.putBoolean("validator.UnclosedWays.test_buildings", True)
pref.putBoolean("validator.CrossingWays.test_highways", True)
pref.putBoolean("validator.CrossingWays.test_waterways_highways", True)
pref.putBoolean("validator.DuplicatedWayNodes.test_highways", True)

from org.openstreetmap.josm.tools import I18n
from org.openstreetmap.josm.io import OsmReader
from org.openstreetmap.josm.gui.progress import NullProgressMonitor
from org.openstreetmap.josm.data.validation.tests import TagChecker, MapCSSTagChecker
from org.openstreetmap.josm.data.validation import ValidationTask

print("Starting QA Bot (HOT TM + Complete Building & Road Rules)...")
sys.stdout.flush()

try:
    I18n.init()
    work_dir = WORK_DIR

    extract_path = work_dir + "/hot_rules"
    mapcss_file = None
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            if file.endswith(".mapcss"):
                mapcss_file = os.path.join(root, file)
                break
        if mapcss_file:
            break

    if not mapcss_file:
        raise RuntimeError("HOT TM MapCSS rules were not prepared before JOSM validation started.")

    custom_mapcss_path = work_dir + "/size_rule.mapcss"
    with open(custom_mapcss_path, "w") as f:
        f.write("""
        meta {
            title: "Custom Bot Rule (Oversize)";
            version: "1.0";
            description: "Detects buildings with an unreasonable size";
        }
        way[building][eval(area()) > 5000] {
            throwWarning: tr("This building is too large (area exceeds 5000 sqm).");
        }
        """)

    target_file = work_dir + "/sample.osm"
    input_stream = FileInputStream(target_file)
    dataset = OsmReader.parseDataSet(input_stream, NullProgressMonitor.INSTANCE)
    input_stream.close()
    primitives = dataset.allPrimitives()
    print("OSM data loaded. Total objects: " + str(primitives.size()))
    sys.stdout.flush()

    mapcss_checker = MapCSSTagChecker()
    try:
        mapcss_checker.addMapCSS("resource://data/validator/geometry.mapcss")
        print("  -> Built-in JOSM geometry MapCSS rules loaded.")
    except Exception as e:
        print("  -> Failed to load built-in geometry.mapcss: " + str(e))

    mapcss_checker.addMapCSS("file:///" + mapcss_file.replace("\\", "/"))
    print("  -> HOT TM MapCSS rules loaded.")
    mapcss_checker.addMapCSS("file:///" + custom_mapcss_path.replace("\\", "/"))
    print("  -> Custom oversize MapCSS rule loaded.")
    sys.stdout.flush()

    test_list = [TagChecker(), mapcss_checker]
    print("Injecting all geometry & tagging validator modules...")
    sys.stdout.flush()

    def try_load(full_class_name):
        try:
            test_class = Class.forName(full_class_name)
            constructor = test_class.getDeclaredConstructors()[0]
            constructor.setAccessible(True)
            instance = constructor.newInstance([])
            test_list.append(instance)
            print("  [OK] Loaded: " + test_class.getSimpleName())
        except java.lang.Throwable as e:
            print("  [FAILED] " + full_class_name + " -> " + str(e))
        except Exception as e:
            print("  [FAILED] " + full_class_name + " -> " + str(e))
        sys.stdout.flush()

    target_classes = [
        "org.openstreetmap.josm.data.validation.tests.DuplicateNode",
        "org.openstreetmap.josm.data.validation.tests.UnclosedWays",
        "org.openstreetmap.josm.data.validation.tests.SelfIntersectingWay",
        "org.openstreetmap.josm.data.validation.tests.OverlappingWays",
        "org.openstreetmap.josm.data.validation.tests.DuplicatedWayNodes",
        "org.openstreetmap.josm.data.validation.tests.RightAngleBuildingTest",
        "org.openstreetmap.josm.data.validation.tests.WayConnectedToArea",
        "org.openstreetmap.josm.data.validation.tests.UntaggedWay",
        "org.openstreetmap.josm.data.validation.tests.CrossingWays$Ways",
        "org.openstreetmap.josm.data.validation.tests.CrossingWays$Boundaries",
        "org.openstreetmap.josm.data.validation.tests.CrossingWays$SelfCrossing"
    ]
    for class_name in target_classes:
        try_load(class_name)

    def populate_ways_used_in_relations(test_instance, ds):
        from java.util import HashSet
        ways_in_relations = HashSet()
        for relation in ds.getRelations():
            for member in relation.getMembers():
                if member.isWay():
                    ways_in_relations.add(member.getWay())
        field = test_instance.getClass().getDeclaredField("waysUsedInRelations")
        field.setAccessible(True)
        field.set(test_instance, ways_in_relations)
        print("  -> Headless fix applied: waysUsedInRelations populated (" + str(ways_in_relations.size()) + " ways).")
        sys.stdout.flush()

    from java.util import ArrayList
    java_primitives = ArrayList(primitives)

    def run_legacy_validation():
        """Compatibility path for JOSM builds where ValidationTask cannot run headlessly."""
        print("Native ValidationTask unavailable; using legacy headless validator path.")
        sys.stdout.flush()
        all_errors = []
        total_tests = len(test_list)
        for idx, test in enumerate(test_list, start=1):
            rule_name = test.getClass().getSimpleName()
            if not rule_name or rule_name == "":
                rule_name = test.getClass().getName().split(".")[-1]
            print("  [" + str(idx) + "/" + str(total_tests) + "] Running " + rule_name + "...")
            sys.stdout.flush()
            t_start = time.time()
            try:
                test.startTest(NullProgressMonitor.INSTANCE)
                if rule_name == "UntaggedWay":
                    populate_ways_used_in_relations(test, dataset)
                test.visit(java_primitives)
                test.endTest()
                errs = test.getErrors()
                found_count = len(errs) if errs else 0
                if errs:
                    all_errors.extend(errs)
                print("      Finished in " + str(round(time.time() - t_start, 2)) + "s -> " + str(found_count) + " issue(s) found.")
                sys.stdout.flush()
            except java.lang.Throwable as t:
                print("  [!] Skipping unstable rule (" + rule_name + "): " + str(t.getMessage()))
                sys.stdout.flush()
            except Exception as e:
                print("  [!] Skipping unstable rule (" + rule_name + "): " + str(e))
                sys.stdout.flush()
        return all_errors

    print("\nStarting validation process (native JOSM ValidationTask)...")
    sys.stdout.flush()
    all_errors = None
    native_error = None

    # ValidationTask is the same execution path used by JOSM's headless ValidatorCLI.
    # It owns test lifecycle, progress monitoring, error collection and cleanup.
    # This keeps QA Buddy aligned with JOSM's supported validation execution model.
    try:
        for test in test_list:
            if test.getClass().getSimpleName() == "UntaggedWay":
                populate_ways_used_in_relations(test, dataset)

        def validation_finished(errors):
            print("  Native ValidationTask finished: " + str(len(errors) if errors else 0) + " issue(s).")
            sys.stdout.flush()

        validation_task = ValidationTask(
            validation_finished,
            NullProgressMonitor.INSTANCE,
            test_list,
            java_primitives,
            None,
            False
        )
        validation_task.run()
        all_errors = list(validation_task.getErrors())
        print("  Native validation completed successfully.")
        sys.stdout.flush()
    except java.lang.Throwable as t:
        native_error = str(t.getMessage())
        print("  [!] Native ValidationTask failed: " + native_error)
        sys.stdout.flush()
    except Exception as e:
        native_error = str(e)
        print("  [!] Native ValidationTask failed: " + native_error)
        sys.stdout.flush()

    if all_errors is None:
        all_errors = run_legacy_validation()

    geojson_output = {"type": "FeatureCollection", "features": []}
    for err in all_errors:
        base_message = err.getMessage()
        severity = err.getSeverity().toString()
        test_name = err.getTester().getName()
        try:
            description = err.getDescription()
        except Exception:
            description = None
        message = base_message + " - " + description if description and description != base_message else base_message
        involved_objects = list(err.getPrimitives())
        if not involved_objects:
            continue
        first_elem = involved_objects[0]
        elem_type = first_elem.getType().toString().lower()
        elem_id = first_elem.getUniqueId()
        obj_id_str = elem_type + "/" + str(elem_id)
        try:
            coor = first_elem.getCoor() if elem_type == "node" else (first_elem.getNode(0).getCoor() if elem_type == "way" and first_elem.getNodesCount() > 0 else None)
            if not coor:
                continue
            lat, lon = coor.lat(), coor.lon()
            josm_url = ""
            if elem_id > 0:
                buf = 0.0003
                josm_url = ("http://127.0.0.1:8111/zoom?left=" + str(lon - buf) + "&right=" + str(lon + buf) + "&top=" + str(lat + buf) + "&bottom=" + str(lat - buf) + "&select=" + elem_type + str(elem_id))
            geojson_output["features"].append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {"rule": test_name, "message": message, "severity": severity, "object_id": obj_id_str, "josm_remote_url": josm_url}
            })
        except Exception:
            pass

    geojson_path = work_dir + "/qa_errors.geojson"
    with open(geojson_path, "w") as f:
        json.dump(geojson_output, f, indent=2)
    print("\nDone! Found " + str(len(geojson_output["features"])) + " issue(s). Saved to: " + geojson_path)
    sys.stdout.flush()
    sys.exit(0)
except Exception:
    traceback.print_exc()
    sys.exit(1)
