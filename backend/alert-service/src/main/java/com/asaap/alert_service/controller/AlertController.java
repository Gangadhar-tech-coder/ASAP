package com.asaap.alert_service.controller;

import com.asaap.alert_service.model.Alert;
import com.asaap.alert_service.payload.AlertRequest;
import com.asaap.alert_service.repository.AlertRepository;
import com.asaap.alert_service.service.EmailService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@CrossOrigin(origins = "*", maxAge = 3600)
@RestController
@RequestMapping("/api/alerts")
public class AlertController {

    @Autowired
    private AlertRepository alertRepository;

    @Autowired
    private EmailService emailService;

    @PostMapping("/trigger")
    public ResponseEntity<?> triggerAlert(@RequestBody AlertRequest alertRequest) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated() || authentication.getPrincipal().equals("anonymousUser")) {
            return ResponseEntity.status(401).body("Unauthorized");
        }

        String userEmail = (String) authentication.getPrincipal();

        Alert alert = new Alert();
        alert.setUserEmail(userEmail);
        alert.setLatitude(alertRequest.getLatitude());
        alert.setLongitude(alertRequest.getLongitude());
        alert.setConfidenceScore(alertRequest.getConfidenceScore());
        alert.setTimestamp(LocalDateTime.now());
        alert.setStatus("TRIGGERED");

        alertRepository.save(alert);

        // Send Email
        if (alertRequest.getEmergencyContactEmail() != null && !alertRequest.getEmergencyContactEmail().isEmpty()) {
            String subject = "URGENT: ASAAP Distress Alert from " + userEmail;
            String text = "A potential distress situation was detected for user: " + userEmail + ".\n" +
                          "Confidence Score: " + alertRequest.getConfidenceScore() + "\n" +
                          "Time: " + alert.getTimestamp() + "\n" +
                          "Location Coordinates: " + alertRequest.getLatitude() + ", " + alertRequest.getLongitude() + "\n\n" +
                          "Please try to contact them immediately or inform local authorities.";
            
            emailService.sendAlertEmail(alertRequest.getEmergencyContactEmail(), subject, text);
        }

        return ResponseEntity.ok("Alert triggered successfully and notifications dispatched.");
    }

    @GetMapping("/history")
    public ResponseEntity<?> getAlertHistory() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated() || authentication.getPrincipal().equals("anonymousUser")) {
            return ResponseEntity.status(401).body("Unauthorized");
        }

        String userEmail = (String) authentication.getPrincipal();
        List<Alert> alerts = alertRepository.findByUserEmailOrderByTimestampDesc(userEmail);

        return ResponseEntity.ok(alerts);
    }
}
