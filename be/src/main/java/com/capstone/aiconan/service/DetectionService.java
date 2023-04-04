package com.capstone.aiconan.service;

import com.capstone.aiconan.repository.DetectionRepository;
import com.capstone.aiconan.response.DetectionResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DetectionService {

    private final DetectionRepository detectionRepository;

    public void recordAbnormals(DetectionResponse response) {

    }
}
