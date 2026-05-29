package com.asaap.alert_service.payload;

import lombok.Data;

@Data
public class AlertRequest {
    private Double latitude;
    private Double longitude;
    private Double confidenceScore;
    private String emergencyContactEmail;
}
