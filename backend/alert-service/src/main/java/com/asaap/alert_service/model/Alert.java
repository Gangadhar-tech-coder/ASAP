package com.asaap.alert_service.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "alerts")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Alert {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String userEmail;

    private Double latitude;
    private Double longitude;
    
    private Double confidenceScore;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    private String status; // TRIGGERED, RESOLVED
}
