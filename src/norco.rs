//! Norco Remote build defaults.
//!
//! Everything that makes this build "Norco Remote" at runtime lives in this one file, so the
//! upstream diff stays small (see NORCO.md at the repository root).
//!
//! It fills the same in-memory tables that upstream's signed "custom client" config fills
//! (`read_custom_client` in `src/common.rs`), which is why `libs/hbb_common` needs no patch.
//!
//! Nothing in here is secret. The key is the server's *public* key.

use hbb_common::config;
use std::sync::Once;

pub const APP_NAME: &str = "Norco Remote";

/// ID/rendezvous server and relay server (hbbs + hbbr on the same host).
pub const SERVER_HOST: &str = "itinventory.norco-inc.com";
/// Console API (device list, heartbeat, sysinfo).
pub const API_SERVER: &str = "https://itinventory.norco-inc.com";
/// Public key of the Norco hbbs. Clients refuse a server that cannot prove it holds the
/// matching private key.
pub const SERVER_PUBLIC_KEY: &str = "Fn4XaHrSvJgqkDV8rov+RsYegwN8XsRa+zszuHr1MVE=";

/// Apply the Norco defaults. Safe to call more than once and from any entry point; it must run
/// before anything reads the server options, so every entry point calls it first.
pub fn apply() {
    static ONCE: Once = Once::new();
    ONCE.call_once(|| {
        *config::APP_NAME.write().unwrap() = APP_NAME.to_owned();

        // Fixed: the user cannot change these, and they win over anything saved on the device.
        {
            let mut fixed = config::OVERWRITE_SETTINGS.write().unwrap();
            for (k, v) in [
                ("custom-rendezvous-server", SERVER_HOST),
                ("relay-server", SERVER_HOST),
                ("api-server", API_SERVER),
                ("key", SERVER_PUBLIC_KEY),
                // Sessions are attended: only the one-time password shown on screen is
                // accepted, so no standing password can be left behind on a reassigned phone.
                ("verification-method", "use-temporary-password"),
            ] {
                fixed.insert(k.to_owned(), v.to_owned());
            }
        }

        // Defaults: a shorter first run. The user can still change these in Settings.
        {
            let mut local = config::DEFAULT_LOCAL_SETTINGS.write().unwrap();
            // The app only talks to Norco's own server, so the generic "are you being scammed"
            // interstitial before the first "Start service" is skipped.
            local.insert("show-scam-warning".to_owned(), "N".to_owned());
            // No "Display over other apps" trip into Android Settings on first start (that page
            // is not reachable on kiosk phones anyway).
            local.insert("disable-floating-window".to_owned(), "Y".to_owned());
        }

        // Phones are supported, they do not support others: hide the "connect to a remote
        // device" side. Remove this to get the normal two-way app back. Android only, so a
        // future desktop build from this fork can still connect out.
        #[cfg(target_os = "android")]
        config::HARD_SETTINGS
            .write()
            .unwrap()
            .insert("conn-type".to_owned(), "incoming".to_owned());
    });
}
