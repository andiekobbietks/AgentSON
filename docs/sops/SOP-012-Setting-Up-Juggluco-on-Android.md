# SOP-012: Setting Up Juggluco on an Android Device

**Status:** Historical device setup notes; follow current official app and sensor instructions.  
**Last reviewed:** 25 November 2026

## Purpose

Provide a generic checklist for configuring a compatible Android device with Juggluco and a supported sensor. This page intentionally avoids person-specific device or health details.

## Prerequisites

- A compatible Android device.
- A sensor and reader supported by the current Juggluco release.
- The sensor manufacturer's instructions.
- Permission from the device owner and the person whose health data is processed.

## Procedure

1. Install Juggluco only from the official source and verify the current release information.
2. Review the app's privacy, security and data-sharing settings.
3. Pair the device and sensor using the manufacturer's and app's current instructions. Sensor application should be performed only by a person trained and authorised to do so.
4. Configure Bluetooth and notifications according to the device and sensor documentation.
5. If cloud upload is enabled, review the destination's security, access controls, retention and data-processing terms first.
6. Use a unique secret for any supported API integration. Store it in the app's protected settings; never paste it into a public document, source file or chat.
7. Verify that readings and timestamps match the source device.

## Safety and privacy

- Health readings are sensitive personal data.
- Do not share screenshots, exports or API credentials without permission.
- Do not rely on a phone or app as the only means of responding to an urgent medical event.
- Contact the app developer or healthcare provider for device-specific troubleshooting.

This SOP is not medical advice and does not validate a particular sensor/app combination.
