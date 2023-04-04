package com.capstone.aiconan.repository;

import com.capstone.aiconan.domain.Abnormal;
import org.springframework.data.repository.CrudRepository;

public interface DetectionRepository extends CrudRepository<Abnormal, Long> {

}
