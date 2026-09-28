#!/usr/bin/python3

import re
import sys

F = sys.argv[1]

with open(F, 'rb') as f:
    content = f.read()

content = re.sub(br'L("([^"\\]|\\.)*")', br'U(\1)', content)
content = re.sub(br'\n(std::string StringFromWideString.*?\n\{[\s\S]+?\})', br'/*\1*/', content)
content = re.sub(br'\n(std::wstring WideStringFromString.*?\n\{[\s\S]+?\})', br'/*\1*/', content)
content = content.replace(b'std::wstring', b'std::string')
content = content.replace(b'std::string_convert', b'std::wstring_convert')

content = content.replace(b'boost/filesystem.hpp', b'filesystem')
content = content.replace(b'boost::filesystem', b'std::filesystem')
content = content.replace(b'#include <windows.h>', b'')
content = content.replace(b'#include <debugapi.h>', b'')
content = content.replace(b'#include <Guiddef.h>', b'')

if F.endswith('AltServerApp.h'):
    content = content.replace(b'GUID _notificationIconGUID;', b'// Windows tray icon is not used on Linux.')

# Newer native libraries can introduce enum values absent from the Windows
# source. Returning no value from an error mapper is undefined behavior.
error_defaults = {
    'InstallError.hpp': (b'return "The app\'s Info.plist could not be found.";',
                         b'default: return std::nullopt;'),
    'DeveloperDiskManager.h': (b'return "DeveloperDiskImage.dmg and its signature could not be found in the downloaded archive.";',
                               b'default: return std::nullopt;'),
}
for filename, (marker, fallback) in error_defaults.items():
    if F.endswith(filename):
        if content.count(marker) != 1:
            raise RuntimeError('Review error fallback: ' + filename)
        content = content.replace(marker, marker + b'\n        ' + fallback)
if F.endswith('ConnectionError.hpp'):
    for marker in (b'case MOBILE_IMAGE_MOUNTER_E_UNKNOWN_ERROR:', b'case DEBUGSERVER_E_UNKNOWN_ERROR:'):
        if content.count(marker) != 1:
            raise RuntimeError('Review native error fallback: ' + marker.decode())
        content = content.replace(marker, b'default: ' + marker)

if F.endswith('AltServerApp.cpp'):

    # MessageBox
    # IDCANCEL
    # fs::path AltServerApp::appDataDirectoryPath
    content = content.replace(b'\r', b'')
    content, count = re.subn(br'AltServerApp::AltServerApp\(\) : _appGroupSemaphore\(1\)\n\{[\s\S]+?\n\}',
                            b'AltServerApp::AltServerApp() : _appGroupSemaphore(1), _helpError(nullptr) {}', content)
    if count != 1:
        raise RuntimeError('Review Linux application initialization after an upstream update')

    content = content.replace(b'#include <windows.h>\n', b'')
    content = content.replace(b'#include <windowsx.h>\n', b'')
    content = content.replace(b'#include <strsafe.h>\n', b'')
    content = content.replace(b'#include <ShlObj_core.h>\n', b'')
    content = content.replace(b'#include <winsparkle.h>\n', b'')
    content = content.replace(b'#pragma comment( lib, "gdiplus.lib" ) \n', b'')
    content = content.replace(b'#include <gdiplus.h> \n', b'')
    content = content.replace(b'#include "resource.h"\n', b'')

    def removePart(content, start, end):
        content, count = re.subn(br'\n' + start + br'[\S\s]+?(' + end + br')', br'\1', content)
        if count != 1:
            raise RuntimeError('Review Linux source transformation: ' + start.decode())
        return content
    # Keep the official source URL / bundle ID configuration between the
    # registry constants and functions. Removing the whole Windows preamble
    # also removed these portable settings when upstream introduced them.
    content = removePart(content, br'const char\* REGISTRY_ROOT_KEY', br'\n#if STAGING')
    content = removePart(content, br'HKEY OpenRegistryKey\(\)', br'\nAltServerApp\* AltServerApp::_instance')
    content = removePart(content, br'static int CALLBACK BrowseFolderCallback', br'\npplx::task<std::shared_ptr<Application>> AltServerApp::InstallApplication')
    content = removePart(content, br'\n.*? AltServerApp::Authenticate', br'\npplx::task<std::shared_ptr<Team>> AltServerApp::FetchTeam')
    content = removePart(content, br'void AltServerApp::ShowNotification', br'\nvoid AltServerApp::ShowErrorAlert')
    # Keep official error descriptions, but display them through the Linux UI.
    content, count = re.subn(br'void AltServerApp::ShowErrorAlert\(std::exception& exception, std::string localizedTitle\)\n\{[\s\S]+?\n\}', br'''void AltServerApp::ShowErrorAlert(std::exception& exception, std::string localizedTitle)
{
    auto error = dynamic_cast<Error*>(&exception);
    this->ShowNotification(localizedTitle, error ? error->localizedDescription() : exception.what());
}''', content)
    if count != 1:
        raise RuntimeError('Review Linux error presentation after an upstream update')
    content = removePart(content, br'bool AltServerApp::CheckDependencies', br'\nfs::path AltServerApp::certificatesDirectoryPath')

    def insertBefore(content, marker, newcontent):
        if content.count(marker) != 1:
            raise RuntimeError('Review Linux insertion point: ' + marker.decode())
        content = content.replace(marker, newcontent + b'\n' + marker)
        return content
    
    content = insertBefore(content, b'AltServerApp* AltServerApp::_instance = nullptr;', br'''
#define IDCANCEL 0
#define MessageBox(x, content, title, xx) (this->ShowAlert(title, std::string(content) + " (Ctrl-C to avoid)"), 1)

// Observes all exceptions that occurred in all tasks in the given range.
template<class T, class InIt>
void observe_all_exceptions(InIt first, InIt last)
{
	// TODO: FIX THIS
}
''')

    content = insertBefore(content, b'fs::path AltServerApp::certificatesDirectoryPath', br'''
HWND AltServerApp::windowHandle() const
{
	return _windowHandle;
}

HINSTANCE AltServerApp::instanceHandle() const
{
	return _instanceHandle;
}


bool AltServerApp::boolValueForRegistryKey(std::string key) const
{
	return false;
}

void AltServerApp::setBoolValueForRegistryKey(bool value, std::string key)
{
	return;
}

std::string AltServerApp::serverID() const
{
	//auto serverID = GetRegistryStringValue(SERVER_ID_KEY);
	//return serverID;
	return "1234567";
}

pplx::task<std::pair<std::shared_ptr<Account>, std::shared_ptr<AppleAPISession>>> AltServerApp::Authenticate(std::string appleID, std::string password, std::shared_ptr<AnisetteData> anisetteData)
{
	auto verificationHandler = [=](void)->pplx::task<std::optional<std::string>> {
		return pplx::create_task([=]() -> std::optional<std::string> {
			std::cout << "Enter two factor code" << std::endl;
			std::string _verificationCode = "";
			std::cin >> _verificationCode;
			auto verificationCode = std::make_optional<std::string>(_verificationCode);
			_verificationCode = "";

			return verificationCode;
		});
	};

	return pplx::create_task([=]() {
		if (anisetteData == NULL)
		{
			throw ServerError(ServerErrorCode::InvalidAnisetteData);
		}

		return AppleAPI::getInstance()->Authenticate(appleID, password, anisetteData, verificationHandler);
	});
}

void AltServerApp::HandleAnisetteError(AnisetteError& error)
{
    this->ShowAlert("AnisetteData error: ", error.localizedDescription());
}

void AltServerApp::ShowNotification(std::string title, std::string message)
{
	std::cout << "Notify: " << title << std::endl << "    " << message << std::endl;
}


extern "C" int getchar();
void AltServerApp::ShowAlert(std::string title, std::string message)
{
	std::cout << "Alert: " << title << std::endl << "    " << message << std::endl;
	std::cout << "Press any key to continue..." << std::endl;
	//char a;
	//std::cin >> a;
	getchar();
}

fs::path AltServerApp::appDataDirectoryPath() const
{
	fs::path altserverDirectoryPath("./AltServerData");

	if (!fs::exists(altserverDirectoryPath))
	{
		fs::create_directory(altserverDirectoryPath);
	}

	return altserverDirectoryPath;
}

void AltServerApp::Start(HWND windowHandle, HINSTANCE instanceHandle)
{
	ConnectionManager::instance()->Start();

	// DeviceManager only needs 
	const char *isNoUSB = getenv("ALTSERVER_NO_SUBSCRIBE");
	if (!isNoUSB) {
		DeviceManager::instance()->Start();
	}
}

void AltServerApp::Stop()
{
}
''')

if F.endswith('DeviceManager.cpp'):
    content = content.replace(b'\r', b'')
    start = b'pplx::task<void> DeviceManager::InstallProvisioningProfiles('
    end = b'pplx::task<void> DeviceManager::RemoveProvisioningProfiles('
    if content.count(start) != 1 or content.count(end) != 1:
        raise RuntimeError('Review provisioning refresh boundaries after an upstream update')
    before, method = content.split(start)
    method, after = method.split(end)
    marker = b'\t\t\tif (activeProfiles.has_value())'
    if method.count(marker) != 1:
        raise RuntimeError('Review provisioning refresh cleanup after an upstream update')
    # Extend the official InstallApp iOS 18 trust fix (5da5175) to profile-only
    # refreshes. Never create a gap with no profiles for the signing identity.
    method = method.replace(marker, b'''            /* Preserve developer trust while replacing profiles on iOS 18+. */
            plist_t versionPlist = NULL;
            char* versionString = NULL;
            OperatingSystemVersion refreshOSVersion = {18, 0, 0};
            if (lockdownd_get_value(client, NULL, "ProductVersion", &versionPlist) == LOCKDOWN_E_SUCCESS && versionPlist != NULL)
            {
                plist_get_string_val(versionPlist, &versionString);
                if (versionString != NULL)
                {
                    try
                    {
                        auto parsedVersion = OperatingSystemVersion(versionString);
                        if (parsedVersion.majorVersion > 0) refreshOSVersion = parsedVersion;
                    }
                    catch (const std::exception&)
                    {
                        // Unknown version: prefer preserving the existing trust.
                    }
                    free(versionString);
                }
            }
            if (versionPlist != NULL) plist_free(versionPlist);

            if (refreshOSVersion.majorVersion >= 18)
            {
                // Install first. If installation fails, retain the existing profiles.
                for (auto& profile : provisioningProfiles)
                {
                    this->InstallProvisioningProfile(profile, mis);
                }
                if (activeProfiles.has_value() && !provisioningProfiles.empty())
                {
                    // Keep active apps and every profile from this request. Only
                    // remove inactive free profiles after replacements succeeded.
                    auto retainedBundleIdentifiers = activeProfiles.value();
                    for (auto& profile : provisioningProfiles)
                    {
                        retainedBundleIdentifiers.insert(profile->bundleIdentifier());
                    }
                    this->RemoveAllFreeProvisioningProfilesExcludingBundleIdentifiers(retainedBundleIdentifiers, mis);
                }
                cleanUp();
                return;
            }

''' + marker)
    content = before + start + method + end + after

if F.endswith('ClientConnection.cpp'):
    old = b'int expectedBytes = *((int32_t*)data.data());'
    if content.count(old) != 1:
        raise RuntimeError('Review request framing after an upstream update')
    content = b'#include "RequestFraming.h"\n' + content.replace(old, b'''int expectedBytes = altserver::requestSize(data);
        if (expectedBytes == 0) throw ServerError(ServerErrorCode::InvalidRequest);''')

sys.stdout.buffer.write(content)
