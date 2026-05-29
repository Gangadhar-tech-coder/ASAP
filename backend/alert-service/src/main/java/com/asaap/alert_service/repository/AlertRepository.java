package com.asaap.alert_service.repository;

import com.asaap.alert_service.model.Alert;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AlertRepository extends JpaRepository<Alert, Long> {
    List<Alert> findByUserEmailOrderByTimestampDesc(String userEmail);
}
