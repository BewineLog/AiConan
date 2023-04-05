package com.capstone.aiconan.repository;

import com.capstone.aiconan.domain.AttackType;
import com.capstone.aiconan.domain.TypeOfAttack;
import org.springframework.data.repository.CrudRepository;

import java.util.Optional;

public interface TypesRepository extends CrudRepository<AttackType, Long> {

    Optional<AttackType> findByName(TypeOfAttack name);
}
