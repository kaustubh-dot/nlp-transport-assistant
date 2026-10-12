# Known limitations

- Transit information comes from a published/static snapshot. Source dates and coverage vary; records do not establish current service operation, and this application must not be presented as live operational transit information.
- Hindi, Roman Hindi and Hinglish recognition remains limited, including mixed scripts, ambiguous place names and complex constraints. Supported input languages do not imply equivalent recognition quality.
- Challenge and regression sets do not support a broad population-level accuracy claim. Successful software tests do not establish multilingual quality or factual travel-answer accuracy.
- Live delays, cancellations and vehicle tracking are unavailable. Confirmed cross-mode transfer graphs, interchange facts, ticket/pass policy and many facility/accessibility values are absent or unverified.
- Route answers use published directional stop sequences. They do not verify real-time operation or optimize an entire journey. Partial source coverage may require clarification or make an answer unavailable.
- Nearest-stop results use straight-line distance, without verified walking paths or walking times. MRTS classification and coverage are limited.
- Fares and timetables are dated records. GTFS times can exceed 24:00 and refer to the service day. Requested modes, dates, times or extra stops can exceed supported evidence.
- Each query is self-contained. Clarifications require a revised complete question; the assistant does not retain conversational slots.
- Curated UI replies are localized, but canonical names, route codes, source IDs, dates and amounts remain unchanged. Unmapped explanations and some Streamlit controls remain English.
- The API is a single-threaded local demonstration server with no public-service authentication or deployment configuration. Verify travel details with the relevant operator.
