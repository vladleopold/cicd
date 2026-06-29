#!/usr/bin/env python3
"""
Comprehensive Unity CI/CD SDK Integration Fixer
"""
import sys, re, pathlib, shutil, json, textwrap

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <Assets_path> <manifest.json_path>")
        sys.exit(1)
    assets = pathlib.Path(sys.argv[1])
    manifest_path = pathlib.Path(sys.argv[2])
    if not assets.exists() or not manifest_path.exists():
        print("Paths not found"); sys.exit(1)
    print("=" * 70)
    print("Unity CI/CD SDK Integration Fixer")
    print("=" * 70)
    remove_gma_editor_stubs(assets)
    add_upm_packages(manifest_path, assets)
    remove_conflicting_asset_sdks(assets, manifest_path)
    remove_sdk_examples(assets)
    fix_dll_metas(assets)
    fix_dotween_modules(assets)
    remove_pixel_perfect_package(manifest_path)
    patch_game_scripts(assets)
    clear_cached_files(assets)
    print("\n" + "=" * 70)
    print("SDK Integration Fix Complete!")
    print("=" * 70)

def remove_gma_editor_stubs(assets):
    print("\n[1/7] Removing GoogleMobileAds/Editor stub files...")
    gma_editor = assets / "GoogleMobileAds" / "Editor"
    if not gma_editor.exists():
        print("  No GoogleMobileAds/Editor found"); return
    stub_indicators = ["stub", "Stub", "namespace GoogleMobileAds.Editor"]
    cs_files = list(gma_editor.rglob("*.cs"))
    if not cs_files: return
    all_are_stubs = all(
        any(i in f.read_text(encoding="utf-8", errors="replace") for i in stub_indicators)
        for f in cs_files if f.stat().st_size < 5000
    )
    if all_are_stubs:
        shutil.rmtree(gma_editor)
        (pathlib.Path(str(gma_editor) + ".meta")).unlink(missing_ok=True)
        print(f"  Removed GoogleMobileAds/Editor stub folder")

def add_upm_packages(manifest_path, assets):
    print("\n[2/7] Adding OpenUPM registry and UPM packages...")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registries = manifest.setdefault("scopedRegistries", [])
    if not any(r.get("url") == "https://package.openupm.com" for r in registries):
        registries.append({"name": "OpenUPM", "url": "https://package.openupm.com", "scopes": ["com.google.ads.mobile", "com.google.external-dependency-manager", "io.sentry.unity"]})
        print("  Added OpenUPM registry")
    else:
        for r in registries:
            if r.get("url") == "https://package.openupm.com":
                if "io.sentry.unity" not in r.get("scopes", []):
                    r.setdefault("scopes", []).append("io.sentry.unity")
                    print("  Added io.sentry.unity to OpenUPM scopes")
    deps = manifest.setdefault("dependencies", {})
    packages = {
        "com.google.ads.mobile": "11.2.0",
        "com.google.external-dependency-manager": "1.2.187",
        "com.zeywin.ads": "https://github.com/zey-win/ZeyWinAdsSDK-Unity.git#v3.9.37",
        "com.crashguard.sdk": "https://github.com/zey-win/CrashGuardSDK-Unity.git#2b3947155206bc445e2d6088ac51cdf2760f921d",
        "com.unity.textmeshpro": "3.0.9",
        "com.unity.mobile.notifications": "2.3.2",
        "io.sentry.unity": "2.2.1",
    }
    added = [f"{p}@{v}" for p, v in packages.items() if p not in deps]
    for p, v in packages.items():
        if p not in deps: deps[p] = v
    if added:
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for p in added: print(f"  Added {p}")

def remove_conflicting_asset_sdks(assets, manifest_path):
    print("\n[3/7] Removing conflicting Assets-based SDK folders...")
    try:
        deps = json.loads(manifest_path.read_text(encoding="utf-8")).get("dependencies", {})
    except: deps = {}
    for pkg, folder in [
        ("com.google.ads.mobile", "GoogleMobileAds"),
        ("com.google.external-dependency-manager", "ExternalDependencyManager"),
        ("com.zeywin.ads", "ZeyWinAds"), ("com.zeywin.ads", "ZeyWin"),
        ("com.zeywin.ads", "UniWebView"), ("com.crashguard.sdk", "CrashGuard"),
        ("com.crashguard.sdk", "CrashGuardSDK"),
    ]:
        if pkg in deps:
            d = assets / folder
            if d.exists():
                shutil.rmtree(d)
                (pathlib.Path(str(d) + ".meta")).unlink(missing_ok=True)
                print(f"  Removed Assets/{folder}")

def remove_sdk_examples(assets):
    print("\n[4/7] Removing SDK examples and demos...")
    for rel in ["FacebookSDK/Examples", "PlayFabSDK/Examples", "IronSource/Demo", "AppLovin/Demo", "MaxSdk/Demos", "GoogleMobileAds/Editor"]:
        d = assets / rel
        if d.exists():
            shutil.rmtree(d)
            (pathlib.Path(str(d) + ".meta")).unlink(missing_ok=True)
            print(f"  Removed Assets/{rel}")

def fix_dll_metas(assets):
    print("\n[5/7] Fixing .dll.meta files...")
    template = textwrap.dedent("""\
    fileFormatVersion: 2
    guid: {guid}
    PluginImporter:
      externalObjects: {{}}
      serializedVersion: 2
      iconMap: {{}}
      executionOrder: {{}}
      defineConstraints: []
      isPreloaded: 0
      isOverridable: 0
      isExplicitlyReferenced: 0
      validateReferences: 1
      platformData:
      - first: {{'': Any}}
        second: {{enabled: 1, settings: {{Exclude Android: 0, Exclude Editor: 0, Exclude Linux64: 1, Exclude OSXUniversal: 1, Exclude Win: 1, Exclude Win64: 1, Exclude iOS: 1}}}}
      - first: {{Any: Editor}}
        second: {{enabled: 1, settings: {{CPU: AnyCPU, DefaultValueInitialized: true, OS: Any}}}}
      userData:
      assetBundleName:
      assetBundleVariant:
    """)
    fixed = 0
    for meta in assets.rglob("*.dll.meta"):
        try: text = meta.read_text(encoding="utf-8", errors="replace")
        except: continue
        if "DefaultImporter" not in text: continue
        m = re.search(r'guid: ([a-f0-9]+)', text)
        meta.write_text(template.format(guid=m.group(1) if m else "0"*32), encoding="utf-8")
        fixed += 1
    if fixed: print(f"  Fixed {fixed} .dll.meta files")

def fix_dotween_modules(assets):
    print("\n[6/7] Fixing DOTween/Modules .asmdef...")
    for m in assets.rglob("DOTween/Modules"):
        if m.is_dir():
            for a in m.rglob("*.asmdef"):
                a.unlink(); (pathlib.Path(str(a)+".meta")).unlink(missing_ok=True)
                print(f"  Removed {a.relative_to(assets) if hasattr(a, 'relative_to') else a.name}")

def patch_game_scripts(assets):
    print("\n[7/9] Patching game scripts for Unity 6000 compatibility...")
    for pattern, search, replace in [
        ("**/GameLocalNotifications.cs", "using Unity.Notifications;", "// using Unity.Notifications;"),
        ("**/SentryCliConfiguration.cs", "using Sentry;", "// using Sentry;"),
    ]:
        for f in assets.glob(pattern):
            text = f.read_text(encoding="utf-8", errors="replace")
            if search in text:
                f.write_text(text.replace(search, replace), encoding="utf-8")
                print(f"  Patched {f.relative_to(assets.parent)}")

def remove_pixel_perfect_package(manifest_path):
    print("\n[8/9] Removing incompatible com.unity.2d.pixel-perfect package...")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    deps = manifest.get("dependencies", {})
    if "com.unity.2d.pixel-perfect" in deps:
        del deps["com.unity.2d.pixel-perfect"]
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("  Removed com.unity.2d.pixel-perfect (incompatible with Unity 6000)")

def clear_cached_files(assets):
    print("\n[9/9] Clearing cached files...")
    root = assets.parent
    for d in [root/"Library/Artifacts", root/"Library/ScriptAssemblies", root/"Library/PackageCache", root/"Temp"]:
        if d.exists():
            shutil.rmtree(d); print(f"  Cleared {d.name}")

if __name__ == "__main__":
    main()
