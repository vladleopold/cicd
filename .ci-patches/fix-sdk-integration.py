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
    generate_build_script(assets)
    clear_cached_files(assets)
    print("\n" + "=" * 70)
    print("SDK Integration Fix Complete!")
    print("=" * 70)

def remove_gma_editor_stubs(assets):
    print("\n[1/10] Removing GoogleMobileAds/Editor stub files...")
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
    print("\n[2/10] Adding OpenUPM registry and UPM packages...")
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
    print("\n[3/10] Removing conflicting Assets-based SDK folders...")
    try:
        deps = json.loads(manifest_path.read_text(encoding="utf-8")).get("dependencies", {})
    except: deps = {}
    GMA_RESOURCE_KEEP = assets / "GoogleMobileAds" / "Resources"
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
                if folder == "GoogleMobileAds":
                    # Keep Resources/ (GoogleMobileAdsSettings.asset)
                    for child in list(d.iterdir()):
                        if child.name == "Resources" or child.suffix == ".meta":
                            continue
                        if child.is_dir():
                            shutil.rmtree(child)
                        else:
                            child.unlink()
                        meta = pathlib.Path(str(child) + ".meta")
                        if meta.exists(): meta.unlink()
                    # Clean up orphaned .meta files not paired with an existing file
                    remaining = {p.stem for p in d.iterdir() if p.suffix != ".meta"}
                    for p in list(d.iterdir()):
                        if p.suffix == ".meta" and p.stem not in remaining:
                            p.unlink()
                    print(f"  Cleaned Assets/{folder} (kept Resources/)")
                else:
                    shutil.rmtree(d)
                    (pathlib.Path(str(d) + ".meta")).unlink(missing_ok=True)
                    print(f"  Removed Assets/{folder}")

def remove_sdk_examples(assets):
    print("\n[4/10] Removing SDK examples and demos...")
    for rel in ["FacebookSDK/Examples", "PlayFabSDK/Examples", "IronSource/Demo", "AppLovin/Demo", "MaxSdk/Demos", "GoogleMobileAds/Editor"]:
        d = assets / rel
        if d.exists():
            shutil.rmtree(d)
            (pathlib.Path(str(d) + ".meta")).unlink(missing_ok=True)
            print(f"  Removed Assets/{rel}")

def fix_dll_metas(assets):
    print("\n[5/10] Fixing .dll.meta files...")
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
    print("\n[6/10] Fixing DOTween/Modules .asmdef...")
    for m in assets.rglob("DOTween/Modules"):
        if m.is_dir():
            for a in m.rglob("*.asmdef"):
                a.unlink(); (pathlib.Path(str(a)+".meta")).unlink(missing_ok=True)
                print(f"  Removed {a.relative_to(assets) if hasattr(a, 'relative_to') else a.name}")

def patch_game_scripts(assets):
    print("\n[7/10] Patching game scripts for Unity 6000 compatibility...")
    for f in assets.glob("**/GameLocalNotifications.cs"):
        text = f.read_text(encoding="utf-8", errors="replace")
        if "using Unity.Notifications;" in text:
            f.write_text(text.replace("using Unity.Notifications;", "// using Unity.Notifications;"), encoding="utf-8")
            print(f"  Patched {f.relative_to(assets.parent)}")
    for f in assets.glob("**/SentryCliConfiguration.cs"):
        f.unlink()
        meta = pathlib.Path(str(f) + ".meta")
        if meta.exists(): meta.unlink()
        print(f"  Removed {f.relative_to(assets.parent)}")

def remove_pixel_perfect_package(manifest_path):
    print("\n[8/10] Removing incompatible com.unity.2d.pixel-perfect package...")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    deps = manifest.get("dependencies", {})
    if "com.unity.2d.pixel-perfect" in deps:
        del deps["com.unity.2d.pixel-perfect"]
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("  Removed com.unity.2d.pixel-perfect (incompatible with Unity 6000)")

def generate_build_script(assets):
    print("\n[9/10] Generating BuildGithubActionsApk build script...")
    editor_dir = assets / "Editor"
    editor_dir.mkdir(parents=True, exist_ok=True)
    script = editor_dir / "BuildGithubActionsApk.cs"
    script.write_text(textwrap.dedent("""\
    using System;
    using System.IO;
    using System.Linq;
    using System.Reflection;
    using UnityEditor;
    using UnityEditor.Build.Reporting;
    using UnityEngine;

    public static class BuildGithubActionsApk
    {
        private const string GmaSettingsAssetPath = "Assets/GoogleMobileAds/Resources/GoogleMobileAdsSettings.asset";

        public static void BuildAndroid()
        {
            var outputPath = GetArg("apkOutputPath");
            var pkgName = GetArg("androidPackageName");
            var versionName = GetArg("androidVersionName");
            var versionCode = GetArg("androidVersionCode");
            var keystorePath = GetArg("androidKeystorePath");

            if (!string.IsNullOrEmpty(pkgName))
                PlayerSettings.SetApplicationIdentifier(BuildTargetGroup.Android, pkgName);
            if (!string.IsNullOrEmpty(versionName))
                PlayerSettings.bundleVersion = versionName;
            if (!string.IsNullOrEmpty(versionCode) && int.TryParse(versionCode, out var vc))
                PlayerSettings.Android.bundleVersionCode = vc;
            if (!string.IsNullOrEmpty(keystorePath) && File.Exists(keystorePath))
            {
                PlayerSettings.Android.keystoreName = keystorePath;
                PlayerSettings.Android.keystorePass = Environment.GetEnvironmentVariable("ANDROID_KEYSTORE_PASS") ?? "";
                PlayerSettings.Android.keyaliasName = Environment.GetEnvironmentVariable("ANDROID_KEYALIAS_NAME") ?? "";
                PlayerSettings.Android.keyaliasPass = Environment.GetEnvironmentVariable("ANDROID_KEYALIAS_PASS") ?? "";
            }

            var zeywinKey = GetArg("zeywinApiKey");
            if (!string.IsNullOrEmpty(zeywinKey))
                EditorPrefs.SetString("ZeyWinApiKey", zeywinKey);

            SetGmaAppId("admobAndroidAppId", "AdMobAndroidAppId");
            SetGmaAppId("admobAndroidAppId", "AdMobAppId");

            var options = new BuildPlayerOptions
            {
                scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
                locationPathName = outputPath ?? "build/Android/Android.apk",
                target = BuildTarget.Android,
                options = BuildOptions.None
            };

            var report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded)
                throw new Exception("Android build failed: " + report.summary.result);
        }

        private static void SetGmaAppId(string argName, string propertyName)
        {
            var value = GetArg(argName);
            if (string.IsNullOrEmpty(value))
                return;

            EditorPrefs.SetString(argName, value);

            var settingsType = AppDomain.CurrentDomain.GetAssemblies()
                .SelectMany(a => a.GetTypes())
                .FirstOrDefault(t => t.Name == "GoogleMobileAdsSettings"
                    && t.Namespace == "GoogleMobileAds.Editor");

            if (settingsType == null)
                return;

            var instanceProp = settingsType.GetProperty("Instance",
                BindingFlags.Public | BindingFlags.Static);
            if (instanceProp == null)
                return;

            var instance = instanceProp.GetValue(null);
            if (instance == null)
                return;

            var prop = settingsType.GetProperty(propertyName,
                BindingFlags.Public | BindingFlags.Instance);
            if (prop != null && prop.CanWrite)
            {
                prop.SetValue(instance, value);
                var saveMethod = settingsType.GetMethod("Save",
                    BindingFlags.Public | BindingFlags.Instance);
                if (saveMethod != null)
                    saveMethod.Invoke(instance, null);
                else
                    EditorUtility.SetDirty((UnityEngine.Object)instance);
                Debug.Log($"[BuildGithubActionsApk] Set {propertyName}={value}");
            }
        }

        public static void BuildAndroidAppBundle()
        {
            EditorUserBuildSettings.buildAppBundle = true;
            BuildAndroid();
        }

        private static string GetArg(string name)
        {
            var args = Environment.GetCommandLineArgs();
            for (var i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "-" + name && i + 1 < args.Length)
                    return args[i + 1];
            }
            return string.Empty;
        }
    }
    """), encoding="utf-8")
    if script.exists():
        print(f"  Generated {script.relative_to(assets.parent)}")

def clear_cached_files(assets):
    print("[10/10] Clearing cached files...")
    root = assets.parent
    for d in [root/"Library/Artifacts", root/"Library/ScriptAssemblies", root/"Library/PackageCache", root/"Temp"]:
        if d.exists():
            shutil.rmtree(d); print(f"  Cleared {d.name}")

if __name__ == "__main__":
    main()
